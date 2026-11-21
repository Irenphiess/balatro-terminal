"""Stable, true-colour, centered alternate-screen TUI with line-diff updates.
Designed for macOS Terminal, iTerm2 and Windows Terminal; no third-party imports.
"""
from __future__ import annotations
import os,sys,unicodedata,shutil,math
if os.name == "nt":
    import msvcrt
else:
    import select,tty,termios
from dataclasses import dataclass
from .content import LOOKUP,JOKERS,VOUCHERS,PACK_KINDS,BOSSES,BOSS_ZH,TAROT_ZH,SPECTRAL_ZH
from .poker import HANDS,HAND_ZH,PLANET_ZH,analyze
from .decks import DECKS,STAKES,stake_index
from .formula import score_formula
from .content_en import description as english_card_description
from .i18n import LANGUAGES, load_language, set_active, localize, tr, active_language, deck_name, deck_desc, stake_name, stake_desc, boss_name, boss_desc

INK=(238,244,225); DIM=(182,210,194); GOLD=(251,214,114); BLACK=(14,25,18)
RED=(252,97,101); ORANGE=(255,170,67); GREEN=(117,248,153); CYAN=(130,233,231)
BLUE=(90,185,255); FOCUS_BG=(29,68,100); VIOLET=(224,169,254); DEEP=(20,53,44); BORDER=(125,166,141)
SUIT={'♥':RED,'♦':ORANGE,'♠':BLACK,'♣':GREEN}
# Balatro game.lua blind definitions (boss_colour); darkened only for legible text.
BOSS_COLOURS={
 'The Ox': tuple(bytes.fromhex('b95b08')),
 'The Hook': tuple(bytes.fromhex('a84024')),
 'The Mouth': tuple(bytes.fromhex('ae718e')),
 'The Fish': tuple(bytes.fromhex('3e85bd')),
 'The Club': tuple(bytes.fromhex('b9cb92')),
 'The Manacle': tuple(bytes.fromhex('575757')),
 'The Tooth': tuple(bytes.fromhex('b52d2d')),
 'The Wall': tuple(bytes.fromhex('8a59a5')),
 'The House': tuple(bytes.fromhex('5186a8')),
 'The Mark': tuple(bytes.fromhex('6a3847')),
 'Cerulean Bell': tuple(bytes.fromhex('009cfd')),
 'The Wheel': tuple(bytes.fromhex('50bf7c')),
 'The Arm': tuple(bytes.fromhex('6865f3')),
 'The Psychic': tuple(bytes.fromhex('efc03c')),
 'The Goad': tuple(bytes.fromhex('b95c96')),
 'The Water': tuple(bytes.fromhex('c6e0eb')),
 'The Eye': tuple(bytes.fromhex('4b71e4')),
 'The Plant': tuple(bytes.fromhex('709284')),
 'The Needle': tuple(bytes.fromhex('5c6e31')),
 'The Head': tuple(bytes.fromhex('ac9db4')),
 'Verdant Leaf': tuple(bytes.fromhex('56a786')),
 'Violet Vessel': tuple(bytes.fromhex('8a71e1')),
 'The Window': tuple(bytes.fromhex('a9a295')),
 'The Serpent': tuple(bytes.fromhex('439a4f')),
 'The Pillar': tuple(bytes.fromhex('7e6752')),
 'The Flint': tuple(bytes.fromhex('e56a2f')),
 'Amber Acorn': tuple(bytes.fromhex('fda200')),
 'Crimson Heart': tuple(bytes.fromhex('ac3232')),
}
def boss_palette(name):
    """Original per-Boss hue with darker screen shades for readable terminal text."""
    rgb=BOSS_COLOURS.get(name,(155,66,99))
    outside=tuple(min(255,8+round(.15*v)) for v in rgb)
    inside=tuple(min(255,14+round(.27*v)) for v in rgb)
    accent=tuple(min(255,90+round(.64*v)) for v in rgb)
    return outside,inside,accent

THEMES={
 'title':((15,43,34),(37,92,67)),
 'blind':((13,48,37),(46,109,77)),
 'play':((14,49,37),(62,132,87)),
 'shop':((21,33,60),(54,74,109)),
 'pack':((20,42,66),(57,97,128)),
 'boss':((52,23,40),(111,49,68)),
 'lost':((51,29,43),(103,50,63)),
 'info':((21,49,60),(48,88,102)),
}
ENH={'Bonus':'额外+30','Mult':'倍率+4','Wild':'万能花色','Glass':'玻璃 ×2','Steel':'钢铁×1.5','Gold':'黄金 +$3','Lucky':'幸运概率','Stone':'石头+50'}
ED={'Foil':'镀箔','Holographic':'镭射','Polychrome':'多彩','Negative':'负片'}
SEAL={'Red':'红印','Gold':'金印','Blue':'蓝印','Purple':'紫印'}
RU={'Common':'普通','Uncommon':'罕见','Rare':'稀有','Legendary':'传说'}

def width(s):
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in ('W','F') or ord(c)>0xFFFF else 1 for c in str(s))

def cut(s,n):
    if n<=0:return ''
    if width(s)<=n:return s
    result=''
    for c in str(s):
        if width(result+c+'…')>n:break
        result+=c
    return result+'…'

def fmt(v):
    try:
        v=int(v)
        return f'{v:,}' if abs(v)<10**12 else f'{str(v)[:3][0]}.{str(v)[:3][1:]}e{len(str(v))-1}'
    except Exception:return str(v)

def name_item(typ,name):
    if not active_language().startswith('zh_'):return name
    if typ=='Joker' and name in LOOKUP:return LOOKUP[name].zh
    if typ=='Tarot':return TAROT_ZH.get(name,name)
    if typ=='Planet':return PLANET_ZH.get(name,name)
    if typ=='Spectral':return SPECTRAL_ZH.get(name,name)
    return name

def card_summary(typ,name,zh_text=''):
    return zh_text if active_language().startswith('zh_') else english_card_description(typ,name)

@dataclass(frozen=True)
class Cell:
    text:str=' '
    fg:tuple=INK
    bg:tuple=DEEP
    bold:bool=False

class Canvas:
    def __init__(self,w,h,bg):
        self.w=w;self.h=h;self.bg=bg
        self.a=[[Cell(bg=bg) for _ in range(w)] for _ in range(h)]
    def rect(self,x,y,w,h,bg):
        for yy in range(max(0,y),min(self.h,y+h)):
            row=self.a[yy]
            for xx in range(max(0,x),min(self.w,x+w)):
                row[xx]=Cell(bg=bg)
    def put(self,x,y,text,fg=INK,bg=None,bold=False):
        if y<0 or y>=self.h:return
        text=localize(text)
        if bg is None:bg=self.bg
        for c in str(text):
            n=width(c)
            if n==0:
                # Combining marks (e.g. strike-through for a forbidden poker hand)
                # belong to the preceding glyph; do not silently drop them.
                px=x-1
                if 0<=px<self.w and self.a[y][px].text:
                    old=self.a[y][px]
                    self.a[y][px]=Cell(old.text+c,old.fg,old.bg,old.bold)
                continue
            if 0<=x<self.w and x+n<=self.w:
                self.a[y][x]=Cell(c,fg,bg,bold)
                if n==2:self.a[y][x+1]=Cell('',fg,bg,bold)
            x+=n
    def centered(self,x,y,w,text,fg=INK,bg=None,bold=False):
        text=localize(text)
        self.put(x+max(0,(w-width(text))//2),y,cut(text,w),fg,bg,bold)
    def right(self,x,y,w,text,fg=INK,bg=None,bold=False):
        text=localize(text)
        self.put(x+max(0,w-width(text)),y,cut(text,w),fg,bg,bold)
    def box(self,x,y,w,h,fg=BORDER,bg=None,title=None,dashed=False):
        if w<3 or h<3:return
        if bg is None:bg=self.bg
        # Terminal character cells are usually about twice as tall as they are
        # wide. Half-density horizontal dashes and full-density vertical dashes
        # therefore have a comparable visual/pixel pitch.
        horizontal=(('┄ ' * ((w-1)//2))[:w-2]) if dashed else '─'*(w-2)
        self.put(x,y,'╭'+horizontal+'╮',fg,bg)
        for row in range(y+1,y+h-1):
            vertical='┆' if dashed else '│'
            self.put(x,row,vertical,fg,bg);self.put(x+w-1,row,vertical,fg,bg)
        self.put(x,y+h-1,'╰'+horizontal+'╯',fg,bg)
        if title:self.put(x+3,y,' '+cut(title,w-9)+' ',GOLD,bg,True)
    def hline(self,x,y,w,fg=BORDER,ch='─',bg=None):
        # A separator inherits the background of the scene/section underneath
        # it rather than Canvas.bg (the OUTER margin colour).
        if not (0<=y<self.h):return
        if bg is None and 0<=x<self.w:bg=self.a[y][x].bg
        self.put(x,y,ch*max(0,w),fg,bg)
    def render_row(self,y):
        buf=[];cur=None
        for cell in self.a[y]:
            if cell.text=='':continue
            st=(cell.fg,cell.bg,cell.bold)
            if st!=cur:
                f,b,bo=st
                buf.append(f'\033[{1 if bo else 22};38;2;{f[0]};{f[1]};{f[2]};48;2;{b[0]};{b[1]};{b[2]}m')
                cur=st
            buf.append(cell.text)
        buf.append('\033[0m')
        return ''.join(buf)

class Renderer:
    def __init__(self):
        self.last=[];self.size=None;self.force=True
    def draw(self,screen):
        sig=(screen.w,screen.h)
        if self.size!=sig:self.force=True;self.size=sig;self.last=[]
        out=[]
        for y,row in enumerate(screen.a):
            if self.force or y>=len(self.last) or self.last[y]!=row:
                out.append(f'\033[{y+1};1H'+screen.render_row(y))
        self.last=[r[:] for r in screen.a];self.force=False
        if out:
            sys.stdout.write(''.join(out)+'\033[?25l');sys.stdout.flush()

class UI:
    """A stage-specific, centrally composed character UI, painted in place."""
    def __init__(self,language='zh_CN'):
        self.renderer=Renderer();self.overlay=None;self.page=0;self.gallery_cursor=0;self.effects_cursor=0
        self.deck_index=0;self.stake_index=0;self.stage='splash';self.cursor_shop=0;self.cursor_pack=0
        self.command='';self.message='方向键 / WASD 选择，Enter 确认'
        self.quit=False;self.last_layout=None
        self.focus='hand';self.cursor_hand=0;self.cursor_joker=0;self.selected_uids=[]
        self.detail=None;self.detail_return=None;self.effects_group=0;self.effects_page=0;self.help_page=0
        self.music_enabled=False;self.music_available=False
        self.inventory_page=0;self.inventory_joker_cursor=0;self.inventory_cursor=0;self.inventory_deck_scroll=0
        self.pending_pack_index=None;self.pending_use_index=None;self.use_return=None;self.inventory_reorder=False
        self.target_cursor=0;self.target_indices=[];self.target_min=0;self.target_max=0
        self.language=language;self.language_cursor=next((i for i,(k,_) in enumerate(LANGUAGES) if k==self.language),0)
        self.language_return=None

    def mode(self,g):
        if self.overlay:return 'info'
        if g is None:return 'title'
        return 'boss' if g.state in ('blind','play') and g.blind==2 else g.state

    def _new_screen(self,g):
        sz=shutil.get_terminal_size((158,57))
        w=max(30,sz.columns-1);h=max(12,sz.lines-1)
        outside,bg=THEMES.get(self.mode(g),THEMES['play'])
        if g is not None and self.mode(g)=='boss':
            outside,bg,_=boss_palette(g.boss)
        c=Canvas(w,h,outside)
        if w<119 or h<49:
            c.centered(0,max(2,h//2-2),w,'终端窗口需要更宽敞的空间',GOLD)
            c.centered(0,max(3,h//2),w,'至少 120 列 × 50 行，推荐 156 列 × 58 行',INK)
            c.centered(0,max(4,h//2+2),w,'Q 退出',DIM)
            return c,None
        W=min(158,w-4);H=min(58,h-2)
        x=(w-W)//2;y=(h-H)//2
        c.rect(x,y,W,H,bg)
        c.box(x,y,W,H,boss_palette(g.boss)[2] if g is not None and self.mode(g)=='boss' else (181,216,193),bg)
        c.put(x+4,y+2,'♠   B A L A T R O   ♥',GOLD,bg,True)
        c.right(x+4,y+2,W-8,'♣  POKER ROGUELIKE  ♦',INK,bg)
        c.hline(x+4,y+4,W-8,BORDER)
        c.hline(x+4,y+H-7,W-8,BORDER)
        self.last_layout=(x,y,W,H)
        self._footer(c,x,y,W,H,bg,g)
        return c,(x,y,W,H,bg)

    def _footer(self,c,x,y,W,H,bg,g):
        c.centered(x+4,y+H-6,W-8,cut(self.message,W-14),GOLD,bg,True)
        c.right(x+4,y+3,W-8,'♫ '+('ON' if self.music_enabled else 'OFF' if self.music_available else 'N/A'),DIM,bg)
        if self.overlay=='detail':guide='E / Enter / Esc 关闭详情，返回刚才的页面'
        elif self.overlay=='language':guide=tr('language_hint',self.language)
        elif self.overlay=='hand':guide='←→/AD 翻页   ↑↓/WS 选牌   Enter 使用效果牌   M 调整 Joker 顺序   E 详情   I/Esc 返回'
        elif self.overlay=='use_target':guide='←→/AD 选择目标   Enter 勾选   P 使用效果牌   Esc 取消'
        elif self.overlay=='pack_target':guide='←→ / AD 移动目标   Enter 选择   P 应用效果   Esc 返回补充包'
        elif self.overlay=='gallery':guide='←→/AD 翻页  ↑↓/WS 选小丑  E 详情  Enter/Esc 返回'
        elif self.overlay=='effects':guide='←→/AD 选类别  ↑↓/WS 选效果并自动翻页  E 详情  Enter/Esc 返回'
        elif self.overlay:guide='Enter / Esc 返回'
        elif g is None:guide=('Enter 进入牌组选择   L 继续游戏   C 音乐   V 语言   Q 退出' if self.stage=='splash' else 'WASD 选牌组   方向键选难度   Enter 创建新局   V 语言   L 读档   Esc 返回封面')
        elif g.state=='blind':guide='Enter 挑战   T 跳过   E 更换 Boss   I 持有卡牌   K 保存   V 语言   H 帮助'
        elif g.state=='play':guide='←→ / AD 移动   ↑↓ / WS 切换 Joker   Enter 选牌   P 出牌   O 弃牌   I 持有卡牌   V 语言'
        elif g.state=='shop':guide='方向键/WASD 选择   Enter 买卖或使用效果牌   E 详情   I 持有卡牌   V 语言   N 下一轮'
        elif g.state=='pack':guide='↑↓ / WS 选择奖励   Enter 领取   E 详情   I 持有卡牌   V 语言   X 牌型等级   Z 放弃'
        else:guide='Enter 返回开屏    L 读档    Q 退出'
        if not self.language.startswith('zh_'):
            if self.overlay=='detail':guide='E / Enter / Esc: close details'
            elif self.overlay=='language':guide=tr('language_hint',self.language)
            elif self.overlay=='hand':guide='A/D: change page · W/S: select · Enter: use consumable · E: details · I/Esc: back'
            elif self.overlay in ('use_target','pack_target'):guide='A/D: move · Enter: select target · P: apply · Esc: cancel'
            elif self.overlay in ('effects','gallery'):guide='A/D: change page/group · W/S: select · E: details · Esc: close'
            elif self.overlay:guide='Enter / Esc: back'
            elif g is None:guide='Enter: start · L: load · C: music · V: language · Q: quit' if self.stage=='splash' else 'WASD: deck · arrows: stake · Enter: start · V: language · L: load'
            elif g.state=='blind':guide='Enter: start Blind · T: skip · E: reroll Boss · I: inventory · K: save · V: language'
            elif g.state=='play':guide='A/D: select cards · W/S: toggle Joker · Enter: select · P: play · O: discard · I: inventory'
            elif g.state=='shop':guide='WASD / arrows: browse · Enter: buy/sell/use · E: inspect · I: inventory · N: next'
            elif g.state=='pack':guide='W/S: select reward · Enter: take · E: inspect · I: inventory · X: hand levels · Z: skip'
            else:guide='Enter: title · L: load save · Q: quit'
        c.centered(x+4,y+H-4,W-8,guide,DIM,bg)
        prompt='›  按键操作中 · H 查看帮助'
        c.centered(x+4,y+H-2,W-8,cut(prompt,W-10),INK,bg,True)

    def _section(self,c,x,y,w,text,bg):
        start=x+2
        c.put(start,y,'✦  '+text+'  ',GOLD,bg,True)
        off=width(text)+7
        c.hline(start+off,y,max(0,w-off-4),BORDER)

    def _text_lines(self,c,x,y,w,text,bg,fg=INK,max_lines=3):
        lines=[];line=''
        for ch in str(text):
            if width(line+ch)>w and line:
                lines.append(line);line=''
            line+=ch
        if line:lines.append(line)
        for i,line in enumerate(lines[:max_lines]):c.put(x,y+i,cut(line,w),fg,bg)
        return min(len(lines),max_lines)

    def draw(self,g):
        set_active(self.language)
        c,outer=self._new_screen(g)
        if outer:
            x,y,W,H,bg=outer
            self.last_layout=(x,y,W,H)
            if self.overlay=='language':self._language_page(c,x,y,W,H,bg)
            elif self.overlay=='detail':self._detail_page(c,x,y,W,H,bg,g)
            elif self.overlay=='pack_target':self._pack_targets(c,x,y,W,H,bg,g)
            elif self.overlay=='use_target':self._use_targets(c,x,y,W,H,bg,g)
            elif self.overlay=='effects':self._effects_page(c,x,y,W,H,bg,g)
            elif self.overlay=='help':self._help(c,x,y,W,H,bg,g)
            elif self.overlay=='gallery':self._gallery(c,x,y,W,H,bg)
            elif self.overlay=='levels' and g:self._levels(c,x,y,W,H,bg,g)
            elif self.overlay=='hand' and g:self._hand_overlay(c,x,y,W,H,bg,g)
            elif g is None:
                if self.stage=='splash':self._splash(c,x,y,W,H,bg)
                else:self._title(c,x,y,W,H,bg)
            else:
                side=34 if W<137 else 36
                self._sidebar(c,x+3,y+6,side,H-15,bg,g)
                rx=x+side+8;rw=W-side-12
                if g.state=='play':self._play(c,rx,y+6,rw,H-15,bg,g)
                elif g.state=='blind':self._blind(c,rx,y+6,rw,H-15,bg,g)
                elif g.state=='shop':self._shop(c,rx,y+6,rw,H-15,bg,g)
                elif g.state=='pack':self._pack(c,rx,y+6,rw,H-15,bg,g)
                elif g.state=='lost':self._lost(c,rx,y+6,rw,H-15,bg,g)
        self.renderer.draw(c)

    def _language_page(self,c,x,y,W,H,bg):
        """Full-page language selection; never overlaps a shop or game screen."""
        title=tr('choose_language',self.language)
        c.centered(x+6,y+7,W-12,f'✦  {title}  /  LANGUAGE  ✦',GOLD,bg,True)
        current=tr('selected_language',self.language)
        c.centered(x+6,y+10,W-12,f'{current}: {dict(LANGUAGES)[self.language]}  ·  {len(LANGUAGES)} languages',DIM,bg)
        visible=min(10,max(4,(H-24)//3))
        self.language_cursor=max(0,min(self.language_cursor,len(LANGUAGES)-1))
        scroll=max(0,min(self.language_cursor-visible+1,len(LANGUAGES)-visible))
        start=self.language_cursor if self.language_cursor<visible else scroll
        if self.language_cursor<visible:start=0
        bx=x+max(8,(W-80)//2);bw=min(W-16,80)
        for row,(code,name) in enumerate(LANGUAGES[start:start+visible]):
            idx=start+row;selected=idx==self.language_cursor
            yy=y+13+row*3
            c.box(bx,yy,bw,3,BLUE if selected else BORDER,bg,dashed=selected)
            flag='✓ ' if code==self.language else '  '
            c.put(bx+3,yy+1,flag+name,BLUE if selected else INK,bg,selected)
            c.right(bx+3,yy+1,bw-7,code,GOLD if code==self.language else DIM,bg)
        c.centered(x+6,y+H-11,W-12,tr('language_hint',self.language),CYAN,bg)
        c.centered(x+6,y+H-10,W-12,f'{self.language_cursor+1} / {len(LANGUAGES)}',DIM,bg)

    def _splash(self,c,x,y,W,H,bg):
        """A dedicated title screen before deck/stake setup."""
        inset=min(W-24,126)
        sx=x+(W-inset)//2
        c.box(sx,y+5,inset,H-14,GOLD,bg)
        c.centered(sx+2,y+8,inset-4,'✦  B A L A T R O  ✦',GOLD,bg,True)
        art=[
            '██████╗  █████╗ ██╗      █████╗ ████████╗██████╗  ██████╗',
            '██╔══██╗██╔══██╗██║     ██╔══██╗╚══██╔══╝██╔══██╗██╔═══██╗',
            '██████╔╝███████║██║     ███████║   ██║   ██████╔╝██║   ██║',
            '██╔══██╗██╔══██║██║     ██╔══██║   ██║   ██╔══██╗██║   ██║',
            '██████╔╝██║  ██║███████╗██║  ██║   ██║   ██║  ██║╚██████╔╝',
            '╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝',
        ]
        for i,line in enumerate(art):c.centered(sx+3,y+12+i,inset-6,line,GOLD if i in (0,5) else INK,bg,True)
        c.centered(sx+4,y+21,inset-8,'╭─────────╮     ╭─────────╮     ╭─────────╮     ╭─────────╮',DIM,bg)
        c.centered(sx+4,y+22,inset-8,'│  A  ♠   │     │  K  ♥   │     │  Q  ♦   │     │  J  ♣   │',GOLD,bg,True)
        c.centered(sx+4,y+23,inset-8,'╰─────────╯     ╰─────────╯     ╰─────────╯     ╰─────────╯',DIM,bg)
        splash_desc=('◇  150 张小丑  ·  15 种牌组  ·  无限底注  ·  赌上一手奇迹  ◇'
                     if self.language.startswith('zh_') else '◇  150 Jokers  ·  15 Decks  ·  Endless Antes  ◇')
        c.centered(sx+4,y+27,inset-8,splash_desc,INK,bg)
        c.centered(sx+4,y+31,inset-8,'╔══════════════════════════════════════════════════╗',BLUE,bg,True)
        enter_text=('║           按  E N T E R  进入游戏              ║'
                    if self.language.startswith('zh_') else '║           Press  E N T E R  to play              ║')
        c.centered(sx+4,y+32,inset-8,enter_text,BLUE,bg,True)
        c.centered(sx+4,y+33,inset-8,'╚══════════════════════════════════════════════════╝',BLUE,bg,True)
        c.centered(sx+4,y+36,inset-8,f'L {tr("continue",self.language)}   V {tr("language",self.language)}   C {tr("music",self.language)}   Q {tr("quit",self.language)}',DIM,bg)

    def _title(self,c,x,y,W,H,bg):
        # Large introductory arcade marquee, not a blank menu.
        title=[
            '╔══════════════════════════════════════════════════╗',
            '║   ♠  ♥             B A L A T R O         ♦  ♣   ║',
            '╚══════════════════════════════════════════════════╝',
        ]
        for i,line in enumerate(title):c.centered(x+5,y+6+i,W-10,line,GOLD,bg,True)
        subtitle=('✦   构筑小丑  ·  升级牌型  ·  挑战不断攀升的盲注目标   ✦'
                  if self.language.startswith('zh_') else '✦  Build Joker combos · Level up poker hands · Beat the Blinds  ✦')
        c.centered(x+5,y+10,W-10,subtitle,INK,bg)
        offset=max(0,(H-48)//4)
        yy=y+13+offset
        self._section(c,x+10,yy,W-20,'选择牌组  ·  WASD 移动',bg)
        grid_y=yy+3
        grid_x=x+10;grid_w=W-20
        cols=5;cw=grid_w//cols
        for i,d in enumerate(DECKS):
            col=i%cols;row=i//cols
            bx=grid_x+col*cw+1;by=grid_y+row*4
            cell_w=cw-2
            selected=i==self.deck_index
            if selected:c.box(bx,by,cell_w,3,BLUE,bg,dashed=True)
            else:c.box(bx,by,cell_w,3,BORDER,bg)
            ink=BLUE if selected else INK
            bg2=bg
            c.centered(bx+1,by+1,cell_w-2,cut(deck_name(d.key,d.name),cell_w-3),ink,bg2,selected)
        focus=DECKS[self.deck_index]
        detail_y=grid_y+12
        c.centered(grid_x,detail_y,grid_w,cut('◆  '+deck_name(focus.key,focus.name)+'   ─   '+deck_desc(focus.key,focus.desc),grid_w),INK,bg)
        # Structure of the currently highlighted starting deck, prior to creating the run.
        if focus.key=='Abandoned Deck':formation='40 张 · ♥10 ♦10 ♠10 ♣10 · 无 J/Q/K'
        elif focus.key=='Checkered Deck':formation='52 张 · ♥26 ♠26 · 无 ♦/♣'
        elif focus.key=='Erratic Deck':formation='52 张 · 点数和花色将在开局随机决定'
        else:formation='52 张 · ♥13 ♦13 ♠13 ♣13 · 每花色 2 到 A'
        if not self.language.startswith('zh_'):
            formation={
              'Abandoned Deck':'40 cards · 10 per suit · no J/Q/K',
              'Checkered Deck':'52 cards · 26 Hearts and 26 Spades only',
              'Erratic Deck':'52 cards · random ranks and suits on new run',
            }.get(focus.key,'52 cards · 13 of each suit · ranks 2 to Ace')
        c.centered(grid_x,detail_y+1,grid_w,('当前牌组牌面构成：' if self.language.startswith('zh_') else 'Starting deck: ')+formation,CYAN,bg)
        stake_y=detail_y+2
        self._section(c,grid_x,stake_y,grid_w,'选择难度  ·  方向键移动',bg)
        sy=stake_y+2
        stake_cw=grid_w//4
        for i,(_,zh,desc) in enumerate(STAKES):
            col=i%4;row=i//4
            bx=grid_x+col*stake_cw+1;by=sy+row*2
            active=i==self.stake_index
            # Stake buttons use just one row each, to avoid touching the footer.
            c.centered(bx,by,stake_cw-2,('◆ ' if active else '  ')+stake_name(STAKES[i][0],zh),BLUE if active else INK,bg,active)
        bottom=sy+5
        if bottom<y+H-7:
            c.centered(grid_x,bottom,grid_w,cut('难度效果：'+stake_desc(STAKES[self.stake_index][0],STAKES[self.stake_index][2]),grid_w),DIM,bg)
        # The title offers a visible resume action when a save exists.
        try:
            from .game import Game
            saves=Game.save_candidates()
            if saves:
                c.centered(x+6,y+H-9,W-12,('✦  按 L 继续游戏  /  Enter 创建新牌局  ✦' if self.language.startswith('zh_') else '✦ L: continue · Enter: new run ✦'),GREEN,bg,True)
            else:
                c.centered(x+6,y+H-9,W-12,('✦  Enter 开始新的牌局  ·  V 语言  ·  C 背景音乐  ✦' if self.language.startswith('zh_') else '✦ Enter: new run · V: language · C: music ✦'),GREEN,bg,True)
        except Exception:pass

    def _sidebar(self,c,x,y,w,h,bg,g):
        sb=tuple(max(0,v-16) for v in bg)
        c.rect(x,y,w,h,sb);c.box(x,y,w,h,BORDER,sb)
        a=x+3;cw=w-6
        c.centered(x,y+2,w,'✦  当 前 牌 局  ✦',GOLD,sb,True)
        dn=next((deck_name(d.key,d.name) for d in DECKS if d.key==g.deck_name),g.deck_name)
        sn=stake_name(g.stake,STAKES[stake_index(g.stake)][1])
        c.centered(x,y+4,w,cut(dn+'  /  '+sn,w-4),INK,sb)
        blind_label=g.blind_name() if self.language.startswith('zh_') else ('Small Blind','Big Blind','Boss Blind')[g.blind]
        c.centered(x,y+6,w,f'ANTE {g.ante:02d}  ·  '+blind_label,CYAN,sb,True)
        c.put(a,y+9,'本轮分数',DIM,sb)
        c.put(a,y+11,cut(fmt(g.score),cw),GOLD,sb,True)
        c.put(a,y+13,'目标分数',DIM,sb)
        c.put(a,y+15,cut(fmt(g.target),cw),INK,sb,True)
        filled=min(cw,int(cw*g.score/max(1,g.target)))
        c.put(a,y+17,'━'*filled,GREEN,sb)
        c.put(a+filled,y+17,'─'*(cw-filled),BORDER,sb)
        c.put(a,y+20,f'金币      $ {g.money}',GOLD,sb,True)
        if g.state in ('play','blind'):
            c.put(a,y+23,f'出牌次数    {g.hands}/{g.max_hands}',INK,sb)
            c.put(a,y+25,f'弃牌次数    {(g.max_discards if g.state=="blind" else g.discards)}/{g.max_discards}',INK,sb)
        else:
            c.put(a,y+23,f'消耗牌槽    {len(g.consumables)}/{g.consumable_slots}',INK,sb)
            c.put(a,y+25,f'优惠券      {len(g.vouchers)}',INK,sb)
        if g.state in ('play','blind'):
            c.put(a,y+27,f'{tr("hand",self.language)} size  {len(g.hand)}/{g.effective_hand_size()}' if not self.language.startswith('zh_') else f'手牌数量    {len(g.hand)}/{g.effective_hand_size()}',INK,sb)
        c.put(a,y+29,f'小丑槽位    {len(g.jokers)}/{g.joker_slots}',INK,sb)
        if h>=37:
            c.put(a,y+31,'即将面对的 BOSS' if self.language.startswith('zh_') else 'Upcoming Boss',CYAN,sb,True)
            c.put(a,y+33,cut(boss_name(g.boss,BOSS_ZH.get(g.boss,'未知')),cw),boss_palette(g.boss)[2],sb,True)
            # Summary is intentionally restricted to one line; the detailed
            # debuff remains on the Blind-select page.
            if h>=40:c.put(a,y+35,cut(boss_desc(g.boss,BOSSES.get(g.boss,'')),cw),DIM,sb)

    def _blind(self,c,x,y,w,h,bg,g):
        self._section(c,x,y,w,'盲注选择  /  BLIND',bg)
        c.centered(x,y+3,w,'ANTE '+str(g.ante)+'   ·   '+('完成盲注赚取金币，进入商店改善构筑' if self.language.startswith('zh_') else 'Beat Blinds to earn money and build your deck'),INK,bg)
        names=['小盲注','大盲注','BOSS 战'] if self.language.startswith('zh_') else ['Small Blind','Big Blind','Boss Blind']
        gap=3;cw=min(28,(w-2*gap-4)//3);tot=3*cw+2*gap
        sx=x+(w-tot)//2
        for i,name in enumerate(names):
            ax=sx+i*(cw+gap);by=y+7
            active=i==g.blind
            boxbg=bg  # Focus is an outline, never a filled selection rectangle.
            c.box(ax,by,cw,10,GOLD if active else BORDER,boxbg)
            c.centered(ax,by+2,cw,name,(boss_palette(g.boss)[2] if i==2 else GOLD) if active else (boss_palette(g.boss)[2] if i==2 else INK),boxbg,True)
            factor=1 if i==0 else 1.5 if i==1 else 2
            if i==2 and g.boss=='The Wall':factor=4
            if i==2 and g.boss=='Violet Vessel':factor=6
            if i==2 and g.boss=='The Needle':factor=1
            if g.deck_name=='Plasma Deck':factor*=2
            c.centered(ax,by+5,cw,fmt(int(g.base_target()*factor)),CYAN,boxbg,True)
            c.centered(ax,by+7,cw,('◈  当前挑战' if self.language.startswith('zh_') else '◈ Current Blind') if active else ('✓  已完成' if i<g.blind else ('即将挑战' if self.language.startswith('zh_') else 'Upcoming')),GREEN if i<g.blind else INK if active else DIM,boxbg)
        boss_y=y+20
        self._section(c,x,boss_y,w,'本 Ante 的 BOSS 能力预告',bg)
        c.centered(x,boss_y+3,w,'♛   '+boss_name(g.boss,BOSS_ZH.get(g.boss,g.boss))+'   ♛',boss_palette(g.boss)[2],bg,True)
        desc=boss_desc(g.boss,BOSSES.get(g.boss,'未设置 Boss'))
        self._text_lines(c,x+6,boss_y+6,w-12,desc,bg,INK,3)
        if g.boss in ('The Ox',):
            c.centered(x,boss_y+9,w,'触发牌型由对局历史决定',DIM,bg)
        elif g.boss=='The Pillar':
            c.centered(x,boss_y+9,w,'已经在本 Ante 出过的牌将受到影响',DIM,bg)
        if boss_y+13<y+h:
            prompt='Enter 开始当前盲注   /   T 跳过小盲注或大盲注'
            c.centered(x,boss_y+13,w,prompt,GOLD,bg,True)
        if any(v in g.vouchers for v in ("Director's Cut",'Retcon')):
            if boss_y+15<y+h:c.centered(x,boss_y+15,w,'E 更换下一个 BOSS（消耗 $10）',CYAN,bg)

    def _joker_board(self,c,x,y,w,bg,g,max_rows=9):
        self._section(c,x,y,w,('小 丑 牌  /  JOKERS  ·  ↑↓/WS 进入 · ←→/AD 选择 · Enter 查看' if self.language.startswith('zh_') else 'JOKERS · W/S: switch · A/D: select · Enter: details'),bg)
        limit=min(len(g.jokers),max_rows)
        if not limit:
            c.centered(x,y+3,w,'尚未拥有小丑牌 · 可以在商店购买',DIM,bg)
            return y+5
        jx=x+max(0,(w-min(100,w-4))//2)
        jw=min(100,w-4)
        name_col=min(28,max(19,jw//3))
        for i,j in enumerate(g.jokers[:limit]):
            yy=y+3+i
            obj=LOOKUP.get(j['name'])
            if not obj:continue
            focused=self.focus=='joker' and i==min(self.cursor_joker,len(g.jokers)-1)
            rarity={'Common':INK,'Uncommon':GREEN,'Rare':VIOLET,'Legendary':GOLD}.get(obj.rarity,INK)
            if focused:
                c.rect(jx,yy,jw,1,FOCUS_BG)
                c.put(jx,yy,'❯',BLUE,FOCUS_BG,True)
            fg=BLUE if focused else rarity
            backing=FOCUS_BG if focused else bg
            flags=[]
            if j.get('eternal'):flags.append('永')
            if j.get('perishable') is not None:flags.append('易')
            if j.get('rental'):flags.append('租')
            if j.get('debuff') or j.get('debuff_round'):flags.append('禁')
            c.put(jx+2,yy,cut(f'{i+1:>2}. '+('??' if g.boss_active('Amber Acorn') else name_item('Joker',j['name'])),name_col-3),fg,backing,True)
            desc=card_summary('Joker',j['name'],obj.desc)+(' ['+''.join(flags)+']' if flags else '')
            if g.boss_active('Amber Acorn'):desc='Face-down Joker' if not self.language.startswith('zh_') else '背面朝上的小丑牌'
            c.put(jx+name_col,yy,cut(desc,jw-name_col-2),INK if focused else DIM,backing)
        return y+4+limit

    def _cards(self,c,x,y,w,bg,hand,hidden=(),locked=None,max_rows=None,selected=(),focus_uid=None,card_width=None,show_number=True,debuffed=()):
        hidden=set(hidden);selected=set(selected);debuffed=set(debuffed);cardw=card_width or 10;cardh=6;gap=1
        if max_rows is not None and card_width is None:
            need=math.ceil(len(hand)/max(1,max_rows))
            for candidate in (10,9,8,7,6):
                if (w+1)//(candidate+1)>=need:cardw=candidate;break
            else:cardw=6
        cols=max(1,min(25,(w+gap)//(cardw+gap)))
        visible=hand if max_rows is None else hand[:max_rows*cols]
        rows=math.ceil(len(visible)/cols)
        for row in range(rows):
            chunk=visible[row*cols:(row+1)*cols]
            total=len(chunk)*cardw+max(0,len(chunk)-1)*gap
            first=x+max(0,(w-total)//2)
            for pos,card in enumerate(chunk):
                idx=row*cols+pos+1;ax=first+pos*(cardw+gap);ay=y+row*(cardh+2)
                focused=focus_uid==card.uid
                picked=card.uid in selected
                if picked:ay-=1
                color=BLUE if focused or picked else SUIT.get(card.suit,INK)
                c.box(ax,ay,cardw,cardh,color,bg,dashed=focused)
                if focused:c.put(ax+max(1,cardw//2),ay,'▼',BLUE,bg,True)
                if card.uid in hidden:
                    c.centered(ax+1,ay+2,cardw-2,'??',GOLD,bg,True)
                else:
                    rank='★' if card.enhancement=='Stone' else card.rank
                    numeric_ink=RED if card.suit in ('♥','♦') else BLACK
                    c.put(ax+2,ay+1,rank,numeric_ink,bg,True)
                    c.centered(ax+1,ay+2,cardw-2,card.suit,SUIT.get(card.suit,INK),bg,True)
                    if show_number:
                        tags=[ENH[card.enhancement]] if card.enhancement in ENH else []
                    else:
                        short={'Bonus':'额外30','Mult':'倍率+4','Wild':'万能','Glass':'玻璃×2','Steel':'钢铁','Gold':'黄金$3','Lucky':'幸运','Stone':'石头50'}
                        tags=[short[card.enhancement]] if card.enhancement in short else []
                    if show_number:
                        tags+=([ED[card.edition]] if card.edition in ED else [])
                        tags+=([SEAL[card.seal]] if card.seal in SEAL else [])
                    c.centered(ax+1,ay+3,cardw-2,cut(' '.join(tags),cardw-2),GOLD if tags else DIM,bg)
                if card.uid in debuffed:
                    # Debuffed cards retain their printed identity for hand
                    # formation but contribute no rank chips or card effects.
                    c.put(ax+max(1,cardw-3),ay+1,'✕',RED,bg,True)
                    c.centered(ax+1,ay+2,cardw-2,'╳',RED,bg,True)
                if show_number:
                    label=str(idx)+(' ✓' if picked else '')+(' ◈' if locked==card.uid else '')
                    c.centered(ax+1,ay+4,cardw-2,label,BLUE if picked or focused else GOLD if locked==card.uid else DIM,bg,picked or focused)
                else:
                    status=[]
                    if card.seal:status.append({'Red':'红','Gold':'金','Blue':'蓝','Purple':'紫'}.get(card.seal,'封'))
                    if card.edition:status.append({'Foil':'箔','Holographic':'镭','Polychrome':'彩','Negative':'负'}.get(card.edition,'版'))
                    if card.bonus:status.append('+'+str(card.bonus))
                    c.centered(ax+1,ay+4,cardw-2,cut('·'.join(status),cardw-2),CYAN if status else DIM,bg,bool(status))
        if len(visible)<len(hand) and max_rows is not None:
            yy=y+rows*(cardh+2)
            if yy<c.h:c.centered(x,yy,w,f'尚有 {len(hand)-len(visible)} 张手牌未显示，按 I 查看全部',GOLD,bg)
        return rows*(cardh+2)

    def score_text(self,result):
        formula=score_formula(result)
        if not self.language.startswith('zh_'):
            key=result.get('hand','')
            label=HAND_ZH.get(key,key)
            if formula.startswith(label+'：'):
                return key+': '+formula[len(label)+1:]
        return formula

    def _play(self,c,x,y,w,h,bg,g):
        self.selected_uids=[uid for uid in self.selected_uids if any(z.uid==uid for z in g.hand)]
        self.cursor_hand=min(self.cursor_hand,max(0,len(g.hand)-1))
        self.cursor_joker=min(self.cursor_joker,max(0,len(g.jokers)-1))
        self._joker_board(c,x,y,w,bg,g,max_rows=10)
        hand_y=y+max(16,7+min(len(g.jokers),10))
        self._section(c,x,hand_y-3,w,('手 牌 · ←→ / AD 移动蓝色虚线焦点  /  Enter 选择' if self.language.startswith('zh_') else 'HAND · A/D: move blue dashed focus · Enter: select'),bg)
        uid=g.hand[self.cursor_hand].uid if self.focus=='hand' and g.hand else None
        used=self._cards(c,x,hand_y,w,bg,g.hand,g.hidden_cards,g.locked_card,
                         max_rows=max(1,(h-(hand_y-y)-2)//8),
                         selected=self.selected_uids,focus_uid=uid,
                         debuffed={card.uid for card in g.hand if g.debuff(card)})
        result_y=hand_y+used+1
        if g.last_result and result_y<y+h-1:
            v=g.last_result
            result=(('⛔ Disallowed: '+boss_desc(g.boss,v['blocked'])) if not self.language.startswith('zh_') else ('⛔ 无法计分：'+v['blocked'])) if v.get('blocked') else self.score_text(v)
            parts=result.split(' × ')
            rows=[];line=parts[0]
            for part in parts[1:]:
                candidate=line+' × '+part
                if width(candidate)>w and line:
                    rows.append(line);line='× '+part
                else:line=candidate
            rows.append(line)
            for j,row in enumerate(rows):
                if result_y+j<y+h-3:
                    c.centered(x,result_y+j,w,cut(row,w),RED if v.get('blocked') else GOLD,bg,True)
        else:rows=[]
        selection_y=result_y+max(2,len(rows)+1)
        if selection_y<y+h:
            chosen=[card for card in g.hand if card.uid in self.selected_uids]
            if chosen:
                kind,_=g.classify(chosen)
                reason=g.blocked_hand_reason(kind,len(chosen))
                formation=(f'当前选中牌型：{HAND_ZH.get(kind,kind)}  Lv.{g.levels.get(kind,1)}' if self.language.startswith('zh_') else f'Selected hand: {kind}  Lv.{g.levels.get(kind,1)}')
            else:
                reason=None;formation=('当前选中牌型：尚未选牌' if self.language.startswith('zh_') else 'Selected hand: no cards selected')
            if reason:
                # Combining strike is drawn through the label itself, not
                # merely through its highlight border.
                crossed=''.join(ch+'\u0336' if ch!=' ' else ch for ch in formation)
                c.centered(x,selection_y,w,cut(crossed+('  ⛔ 无法计分' if self.language.startswith('zh_') else '  ⛔ Cannot score'),w),RED,bg,True)
                if selection_y+1<y+h:
                    c.centered(x,selection_y+1,w,cut(reason if self.language.startswith('zh_') else boss_desc(g.boss,reason),w),RED,bg,True)
            else:
                c.centered(x,selection_y,w,cut(formation+(f'  ·  已选 {len(chosen)} / 5  ·  P 出牌  ·  O 弃牌  ·  X 牌型等级' if self.language.startswith('zh_') else f'  ·  {len(chosen)} / 5 selected  ·  P play  ·  O discard  ·  X levels'),w),BLUE if chosen else DIM,bg,True)


    def shop_shows_owned(self,g):
        """Kept for compatibility: owned cards are ALWAYS navigable; scrolling is unlimited."""
        return bool(g and g.state=='shop' and (g.jokers or g.consumables))

    def shop_entries(self,g):
        if g is None or g.state!='shop':return []
        options=[('owned_joker',i) for i in range(len(g.jokers))]
        options.extend(('owned_consumable',i) for i in range(len(g.consumables)))
        options.extend(('card',i) for i in range(len(g.shop)))
        options.extend(('pack',i) for i in range(len(g.packs)))
        if g.shop_voucher:options.append(('voucher',0))
        return options

    def _shop(self,c,x,y,w,h,bg,g):
        self._section(c,x,y,w,'商  店  /  SHOP',bg)
        c.centered(x,y+3,w,('方向键 / WASD 选择   E 详情   Enter 买入 / 出售 / 使用效果   N 离开商店' if self.language.startswith('zh_') else 'WASD / arrows: select · E: details · Enter: buy / sell / use · N: next'),INK,bg)
        entries=self.shop_entries(g)
        self.cursor_shop=min(max(0,self.cursor_shop),max(0,len(entries)-1))
        c.centered(x,y+4,w,f'可选择项目 {self.cursor_shop+1 if entries else 0} / {len(entries)} · 全部持有牌均可滚动查看',DIM,bg)
        a=x+max(3,(w-min(w-6,92))//2);aw=min(w-6,92)
        sections=(('owned_joker','已 持 有 小 丑 牌  /  Enter 出售'),
                  ('owned_consumable','已 持 有 效 果 牌  /  Enter 使用'),
                  ('card','单 张 卡 牌'),('pack','补 充 包'),('voucher','优 惠 券'))
        # Every shop option uses the same three-row bordered card as inventory.
        # Scroll whole card/heading rows rather than stripping borders on small terminals.
        items=[]
        for cat,title in sections:
            choices=[(idx,ind) for idx,(typ,ind) in enumerate(entries) if typ==cat]
            if choices:items.append(('heading',title,None))
            for global_index,internal in choices:items.append(('entry',global_index,internal))
        total=sum(2 if typ=='heading' else 3 for typ,*_ in items)
        available=h-11
        preceding=0;focused_end=0
        for kind,v,_ in items:
            height=2 if kind=='heading' else 3
            if kind=='entry' and v==self.cursor_shop:focused_end=preceding+height
            preceding+=height
        shift=max(0,focused_end-available)
        shift=min(shift,max(0,total-available))
        yy=y+6-shift
        for kind,value,internal in items:
            if kind=='heading':
                if y+5<=yy<y+h-3:self._section(c,a,yy,aw,value,bg)
                yy+=2;continue
            typ,_=entries[value]
            if typ=='owned_joker':
                j=g.jokers[internal];obj=LOOKUP[j['name']];name=name_item('Joker',j['name'])
                price=j.get('sell',max(1,obj.cost//2))
                sub=('出售获得 $' if self.language.startswith('zh_') else 'Sell for $')+str(price)+'  ·  '+card_summary('Joker',j['name'],obj.desc)
                if j.get('eternal'):sub=('永恒小丑不可出售' if self.language.startswith('zh_') else 'Eternal: cannot sell')+'  ·  '+card_summary('Joker',j['name'],obj.desc)
            elif typ=='owned_consumable':
                item=g.consumables[internal]
                name=name_item(item['type'],item['name'])
                price='持有';sub='Enter 使用 · '+self.pack_brief(item,g)
            elif typ=='card':
                item=g.shop[internal];name=name_item(item['type'],item['name']);price=item['cost']
                sub=card_summary('Joker',item['name'],LOOKUP[item['name']].desc) if item['type']=='Joker' else {'Planet':'永久升级一个牌型','Tarot':'修改卡牌或资源','Spectral':'特殊效果','Card':'将扑克牌加入牌组'}.get(item['type'],'')
                if not self.language.startswith('zh_') and item['type']!='Joker':
                    sub={'Planet':'Permanently level up a poker hand','Tarot':'Modify cards or resources','Spectral':'Unusual effects, sometimes with a cost','Card':'Add a playing card to your deck'}.get(item['type'],sub)
            elif typ=='pack':
                item=g.packs[internal]
                if self.language.startswith('zh_'):name={'Normal':'普通','Jumbo':'大型','Mega':'巨型'}[item['size']]+PACK_KINDS[item['kind']]
                else:name=item['size']+' '+item['kind']+' Pack'
                price=item['cost'];sub='打开补充包并挑选奖励'
            else:
                name=('优惠券 · '+VOUCHERS[g.shop_voucher]['desc'] if self.language.startswith('zh_') else 'Voucher · '+g.shop_voucher)
                price=g.apply_cost(10);sub='购买后持续生效'
            active=value==self.cursor_shop
            if y+5<=yy and yy+2<y+h-3:
                c.box(a+1,yy,aw-2,3,BLUE if active else BORDER,bg,dashed=active)
                c.put(a+3,yy+1,'➤' if active else '·',BLUE if active else DIM,bg,active)
                c.put(a+6,yy+1,cut(name,aw-28),BLUE if active else INK,bg,active)
                c.right(a+3,yy+1,aw-8,('售 $' if typ=='owned_joker' else '' if typ=='owned_consumable' else '$')+str(price),GOLD,bg,True)
                c.put(a+6,yy+2,' '+cut(sub,aw-16)+' ',CYAN if active else DIM,bg)
            yy+=3
        if not entries:c.centered(x,y+h-4,w,'已售完 · 按 N 进入下一轮',DIM,bg)
        c.centered(x,y+h-1,w,cut(('全部已持有 Joker / 效果牌均可滚动选中   ·   E 详情  ·  Enter 确认  ·  N 下一轮' if self.language.startswith('zh_') else 'Scroll through all owned cards · E: details · Enter: confirm · N: next round'),w),BLUE,bg)

    @staticmethod
    def pack_brief(item,g):
        if not active_language().startswith('zh_'):
            return english_card_description(item.get('type',''),item.get('name',''))
        """Short effect preview, shown for ALL rewards, including focused rewards."""
        from .explain import TAROT_DETAIL,SPECTRAL_DETAIL
        typ,name=item['type'],item['name']
        if typ=='Joker':
            return LOOKUP[name].desc if name in LOOKUP else '特殊小丑效果'
        if typ=='Planet':
            lev=g.levels.get(name,1)
            a=HANDS.get(name,(0,0,0,0))
            return f'{HAND_ZH.get(name,name)} 升至 Lv.{lev+1} · 基础筹码 +{a[2]} / 倍率 +{a[3]}'
        if typ=='Tarot':return TAROT_DETAIL.get(name,'改变手牌属性或资源')
        if typ=='Spectral':return SPECTRAL_DETAIL.get(name,'特殊能力；可能包含代价')
        if typ=='Card':
            card=item.get('card',{})
            return f"新扑克牌 {card.get('rank','?')}{card.get('suit','')}  ·  {ENH.get(card.get('enhancement',''),'普通牌')}"
        return '当前奖励可按 E 查看详细说明'

    def _pack(self,c,x,y,w,h,bg,g):
        p=g.pack
        if not p:return
        self._section(c,x,y,w,'补充包  /  '+(PACK_KINDS[p['kind']] if self.language.startswith('zh_') else p['kind']+' Pack'),bg)
        total=p.get('original_total',len(p['options']))
        c.centered(x,y+3,w,(f'剩余可选 {p["picks"]} 张 / 共 {total} 个候选   ·   ↑↓ / WS 移动   Enter 选择   E 详情' if self.language.startswith('zh_') else f'Picks left: {p["picks"]} / {total} options · W/S: move · Enter: take · E: details'),GOLD,bg,True)
        a=x+max(4,(w-min(w-8,85))//2);aw=min(w-8,85)
        self.cursor_pack=min(max(0,self.cursor_pack),max(0,len(p['options'])-1))
        stride=4;card_height=3
        for idx,item in enumerate(p['options']):
            yy=y+6+idx*stride
            if yy+card_height>y+h-2:break
            label=name_item(item['type'],item['name'])
            focused=(idx==self.cursor_pack)
            c.box(a,yy,aw,card_height,BLUE if focused else BORDER,bg,dashed=focused)
            c.put(a+3,yy+1,'➤' if focused else '·',BLUE if focused else DIM,bg,focused)
            c.put(a+6,yy+1,cut(f'{idx+1}.  '+label,aw-11),BLUE if focused else INK,bg,True)
            # One-row interior: the summary is directly on the lower edge, no blank row.
            brief=' '+cut(self.pack_brief(item,g),aw-15)+' '
            c.put(a+6,yy+card_height-1,brief,CYAN if focused else DIM,bg)
        if p['kind'] in ('Arcana','Spectral') and g.hand:
            hand_y=y+max(26,8+stride*len(p['options']))
            cols=max(1,min(10,(w+1)//11))
            actual_height=2+math.ceil(len(g.hand)/cols)*8
            if hand_y+actual_height<y+h-1:
                self._section(c,x,hand_y,w,'效果目标 / 手牌',bg)
                self._cards(c,x,hand_y+2,w,bg,g.hand,max_rows=2)
            elif y+h-2>y+6+len(p['options'])*stride:
                c.centered(x,y+h-2,w,'需要指定手牌时，Enter 会打开独立目标选择页',DIM,bg)

    def _pack_targets(self,c,x,y,W,H,bg,g):
        """Full-screen target picker so it never overlaps the pack or the shop."""
        if not g or g.state!='pack' or not g.pack or self.pending_pack_index is None:return
        idx=self.pending_pack_index
        if idx>=len(g.pack['options']):return
        item=g.pack['options'][idx]
        c.centered(x+4,y+8,W-8,'✦  选 择 效 果 目 标  ✦',GOLD,bg,True)
        c.centered(x+4,y+11,W-8,name_item(item['type'],item['name']),CYAN,bg,True)
        c.centered(x+4,y+14,W-8,f'需要选择 {self.target_min} 至 {self.target_max} 张手牌   ·   已选择 {len(self.target_indices)} 张',GOLD,bg)
        fx=x+8;fw=W-16
        focused=g.hand[self.target_cursor].uid if g.hand else None
        picked={g.hand[i].uid for i in self.target_indices if i<len(g.hand)}
        self._cards(c,fx,y+21,fw,bg,g.hand,max_rows=2,selected=picked,focus_uid=focused)
        c.centered(x+8,y+H-10,W-16,'←→ / AD 移动   Enter 选择目标   P 确认应用   Esc 取消',BLUE,bg,True)
        if item['name']=='Death':
            c.centered(x+8,y+H-9,W-16,'「死神」按选择顺序操作：第一张牌变成第二张牌',DIM,bg)

    def _use_targets(self,c,x,y,W,H,bg,g):
        """Inventory consumable targeting: dedicated screen, never overlays other panes."""
        if not g or self.pending_use_index is None or not 0<=self.pending_use_index<len(g.consumables):return
        item=g.consumables[self.pending_use_index]
        c.centered(x+4,y+8,W-8,'✦  效 果 牌 · 选 择 生 效 目 标  ✦',GOLD,bg,True)
        c.centered(x+4,y+11,W-8,name_item(item['type'],item['name']),CYAN,bg,True)
        c.centered(x+4,y+14,W-8,f'选择 {self.target_min}～{self.target_max} 张牌  ·  已选 {len(self.target_indices)} 张',GOLD,bg)
        focused=g.hand[self.target_cursor].uid if g.hand else None
        picked={g.hand[i].uid for i in self.target_indices if i<len(g.hand)}
        self._cards(c,x+8,y+21,W-16,bg,g.hand,max_rows=2,selected=picked,focus_uid=focused)
        c.centered(x+8,y+H-10,W-16,'←→ / AD 移动  ·  Enter 选择  ·  P 确认使用  ·  Esc 取消',BLUE,bg,True)
        if item['name']=='Death':
            c.centered(x+8,y+H-9,W-16,'死神：第一张目标牌变为第二张目标牌',DIM,bg)

    def _lost(self,c,x,y,w,h,bg,g):
        c.centered(x,y+6,w,'╔════════════════════════════╗',RED,bg,True)
        c.centered(x,y+8,w,'║     G A M E   O V E R      ║',RED,bg,True)
        c.centered(x,y+10,w,'╚════════════════════════════╝',RED,bg,True)
        c.centered(x,y+15,w,'这次的牌局到此结束。',INK,bg)
        c.centered(x,y+20,w,f'ANTE {g.ante}    ·    {fmt(g.score)} / {fmt(g.target)}',GOLD,bg,True)
        if g.last_result:
            c.centered(x,y+23,w,cut('最后一手  '+self.score_text(g.last_result),w),CYAN,bg,True)
        c.centered(x,y+25,w,'Enter 返回开屏    L 读取存档',CYAN,bg)

    def _help(self,c,x,y,W,H,bg,g):
        """Context-sensitive shortcuts listed once by key, not legacy number recipes."""
        c.centered(x+4,y+7,W-8,'操  作  指  南',GOLD,bg,True)
        actions=[
          ('Enter','确认选项；战斗选牌、商店买卖、补充包领取、I 中使用效果牌'),
          ('WASD','除开局设置外，等同 ↑ ↓ ← →'),
          ('开局设置','WASD 选牌组；方向键选难度'),
          ('P / O','战斗：打出/弃掉已选手牌；效果牌目标页按 P 确认'),
          ('E','商店/补充包/I 看当前焦点牌的详情；再次 E 关闭；准备阶段更换 Boss'),
          ('I','查看持有 Joker 与效果牌，最后一页看完整牌组；在 I 中 Enter 使用效果牌'),
          ('X','查看牌型组合、当前等级及升级收益'),
          ('H','显示/关闭本帮助'),
          ('T','跳过小盲注或大盲注'),
          ('N','离开商店，进入下一盲注'),
          ('R','商店重新随机商品'),
          ('Z','结束当前补充包的剩余选择'),
          ('M','I 界面选中 Joker 后进入排序模式，W/S 调整，M 结束'),
          ('Backspace','I 界面选中 Joker 后出售；可解除翠绿叶片 Boss 的禁用效果'),
          ('F','查看塔罗、星球、幻灵等效果牌图鉴'),
          ('G','查看 Joker 图鉴'),
          ('K','立即保存游戏'),
          ('L','读取当前版本游戏存档'),
                    ('C','开启/关闭随场景变化的背景音乐'),
          ('V','语言 / Language：打开语言选择页，W/S 选择，Enter 确认'),
          ('Q','保存并退出'),
          ('Esc','关闭详情或菜单、返回上一画面'),
        ]
        if not self.language.startswith('zh_'):
            actions=[
              ('Enter','Confirm · select a hand card · buy/sell · choose a pack reward'),
              ('WASD','Same as the arrow keys (except deck/stake setup)'),
              ('Deck setup','WASD: choose deck · arrow keys: choose stake'),
              ('P / O','Play / discard selected cards · P applies targeted effects'),
              ('E','Details of focused item · E again to close · reroll Boss'),
              ('I','Owned Jokers & consumables · final page: entire deck'),
              ('X','Poker hands, levels, chips and multipliers'),
              ('H','Toggle this help screen'),
              ('T','Skip Small or Big Blind'),
              ('N','Leave the shop and continue'),
              ('R','Reroll the shop'),
              ('Z','Skip remaining pack choices'),
              ('M','Reorder Joker in Inventory; W/S changes position'),
              ('Backspace','Sell focused Joker in Inventory (including during Boss battles)'),
              ('F / G','Consumable / Joker collections'),
              ('K / L','Save game / load save'),
              ('C','Toggle scene-based music'),
              ('V','Change language; W/S, arrows, Enter to apply'),
              ('Q','Save and quit'),
              ('Esc','Close an overlay or cancel target selection'),
            ]
        cw=(W-24)//2;left=x+10;right=left+cw+4
        rows=max(8,min(16,(H-20)//2))
        page_len=rows*2
        total=max(1,math.ceil(len(actions)/page_len))
        self.help_page=max(0,min(total-1,self.help_page))
        shown=actions[self.help_page*page_len:(self.help_page+1)*page_len]
        for i,(shortcut,desc) in enumerate(shown):
            col=i//rows;row=i%rows
            bx=left if col==0 else right;by=y+11+row*2
            c.put(bx,by,shortcut,GOLD,bg,True)
            c.put(bx+12,by,cut(desc,cw-15),INK,bg)
        title=f'帮助 {self.help_page+1}/{total}  ·  Enter / Esc 返回'
        if total>1:title+='  ·  ←→ / AD 翻页'
        c.centered(x+5,y+H-10,W-10,title,DIM,bg)

    def _gallery(self,c,x,y,W,H,bg):
        pages=math.ceil(len(JOKERS)/12);self.page=max(0,min(pages-1,self.page))
        c.centered(x+4,y+7,W-8,f'小 丑 图 鉴   /   {self.page+1:02d}  /  {pages:02d}',GOLD,bg,True)
        a=x+max(9,(W-105)//2)
        for pos,j in enumerate(JOKERS[self.page*12:(self.page+1)*12]):
            yy=y+11+pos*2;active=pos==self.gallery_cursor
            c.put(a,yy,('➤' if active else '·')+f' {self.page*12+pos+1:>3}.  '+cut(name_item('Joker',j.name),20),BLUE if active else GOLD,bg,True)
            c.put(a+30,yy,cut(card_summary('Joker',j.name,j.desc),min(70,W-54)),BLUE if active else INK,bg)
        c.centered(x+4,y+H-10,W-8,('←→ / AD 翻页    ↑↓ / WS 选择 Joker    E 当前焦点详情    Enter / Esc 返回' if self.language.startswith('zh_') else 'A/D: page · W/S: select Joker · E: details · Enter/Esc: back'),DIM,bg)

    def _levels(self,c,x,y,W,H,bg,g):
        c.centered(x+4,y+7,W-8,'牌 型 组 合 与 等 级  /  POKER HANDS',GOLD,bg,True)
        a=x+max(5,(W-119)//2)
        combos={
          'High Card':'不构成其他牌型', 'Pair':'两张点数相同', 'Two Pair':'两组对子',
          'Three of a Kind':'三张相同点数','Straight':'五张点数连续','Flush':'五张花色相同',
          'Full House':'三条 + 一对','Four of a Kind':'四张相同点数',
          'Straight Flush':'同花 + 顺子','Five of a Kind':'五张相同点数',
          'Flush House':'同花 + 葫芦','Flush Five':'同花 + 五条',
        }
        for i,(name,(chip,mult,ci,mi)) in enumerate(HANDS.items()):
            yy=y+11+i*2
            lv=g.levels[name]
            c.put(a,yy,cut(HAND_ZH[name] if self.language.startswith('zh_') else name,17),INK,bg,True)
            c.put(a+19,yy,f'Lv.{lv:>3}',CYAN,bg)
            c.put(a+29,yy,f'{chip+ci*(lv-1):>5} 筹码 ×{mult+mi*(lv-1):>3}',GOLD,bg)
            c.put(a+54,yy,PLANET_ZH[name] if self.language.startswith('zh_') else __import__('arcana.poker',fromlist=['PLANETS']).PLANETS[name],DIM,bg)
            c.put(a+74,yy,cut(combos[name],W-87),DIM,bg)
        c.centered(x+4,y+H-10,W-8,'Enter / Esc 返回',DIM,bg)

    def inventory_capacity(self):
        H=self.last_layout[3] if self.last_layout else 54
        return max(4,(H-27)//3)

    def inventory_entries(self,g):
        """Full equipped inventory, including every Joker and consumable."""
        if not g:return []
        return [('joker',i) for i in range(len(g.jokers))]+[('consumable',i) for i in range(len(g.consumables))]

    def inventory_pages(self,g):
        return max(1,math.ceil(len(self.inventory_entries(g))/self.inventory_capacity()))+1

    def inventory_page_entries(self,g):
        start=self.inventory_page*self.inventory_capacity()
        return self.inventory_entries(g)[start:start+self.inventory_capacity()]

    def inventory_is_deck(self,g):
        return self.inventory_page==self.inventory_pages(g)-1

    @staticmethod
    def _deck_by_suit(g):
        from .cards import RANKS
        rank={r:i for i,r in enumerate(RANKS)}
        order=('♥','♦','♠','♣')
        cards={s:[] for s in order}
        for card in g.deck:
            if card.suit in cards:cards[card.suit].append(card)
        for s in order:cards[s].sort(key=lambda c:(rank.get(c.rank,99),c.uid))
        return cards

    def deck_visual_rows(self,g,W=None):
        """Physical rows of real card tiles, ordered by suit then rank."""
        suits=self._deck_by_suit(g)
        inner=(W if W is not None else (self.last_layout[2] if self.last_layout else 158))-27
        per_row=max(1,(inner+1)//9)  # Eight-cell cards with one-cell spacing.
        result=[]
        for suit in ('♥','♦','♠','♣'):
            values=suits[suit]
            if not values:result.append((suit,[],True));continue
            for i in range(0,len(values),per_row):
                result.append((suit,values[i:i+per_row],i==0))
        return result

    @staticmethod
    def deck_visible_rows(H):
        # Reserve space for page header, scroll status and the global footer.
        return max(1,(H-27)//7)

    def _hand_overlay(self,c,x,y,W,H,bg,g):
        """Inventory pages first, the entire deck as horizontal playing cards last."""
        n=self.inventory_pages(g)
        self.inventory_page=max(0,min(self.inventory_page,n-1))
        ax=x+8;cw=W-16
        c.centered(ax,y+7,cw,(f'✦  我 的 持 有 卡 牌  ·  {self.inventory_page+1}/{n}  ✦' if self.language.startswith('zh_') else f'✦ MY CARDS · {self.inventory_page+1}/{n} ✦'),GOLD,bg,True)
        if self.inventory_is_deck(g):
            self._section(c,ax,y+10,cw,f'整 套 牌 组   ·   {len(g.deck)} 张牌  ·  包含已购买和改造的牌',bg)
            visual=self.deck_visual_rows(g,W)
            view=self.deck_visible_rows(H)
            maximum=max(0,len(visual)-view)
            self.inventory_deck_scroll=max(0,min(maximum,self.inventory_deck_scroll))
            base=y+13
            for row,(suit,cards,first) in enumerate(visual[self.inventory_deck_scroll:self.inventory_deck_scroll+view]):
                yy=base+row*7
                c.put(ax+2,yy+2,suit,SUIT.get(suit,INK),bg,True)
                if first:c.put(ax+4,yy+2,'·',DIM,bg)
                self._cards(c,ax+10,yy,cw-12,bg,cards,card_width=8,show_number=False)
            c.centered(ax,y+H-12,cw,
                       f'四花色 · 2 → A   |   ↑↓ / WS 浏览   |   第 {self.inventory_deck_scroll+1}–{min(len(visual),self.inventory_deck_scroll+view)} / {len(visual)} 排',CYAN,bg)
        else:
            entries=self.inventory_page_entries(g)
            self.inventory_cursor=max(0,min(self.inventory_cursor,max(0,len(entries)-1)))
            self._section(c,ax,y+10,cw,(f'持有 Joker {len(g.jokers)} 张   /   消耗牌 {len(g.consumables)} 张   ·  ↑↓ / WS 选择' if self.language.startswith('zh_') else f'Jokers: {len(g.jokers)} · Consumables: {len(g.consumables)} · W/S: select'),bg)
            if not entries:
                c.centered(ax,y+16,cw,'暂无持有 Joker 或消耗牌。下一页可以查看整副牌组。',DIM,bg)
            boxx=ax+3;boxw=cw-6
            for slot,(typ,idx) in enumerate(entries):
                yy=y+13+3*slot
                focused=slot==self.inventory_cursor
                bg2=bg  # no saturated blue fill; only a blue outline
                c.box(boxx,yy,boxw,3,BLUE if focused else BORDER,bg2,dashed=focused)
                if typ=='joker':
                    item=g.jokers[idx];obj=LOOKUP.get(item['name'])
                    name=name_item('Joker',item['name']) if obj else item['name']
                    desc=card_summary('Joker',item['name'],obj.desc) if obj else 'Joker'
                    flags=[]
                    if item.get('eternal'):flags.append('永恒')
                    if item.get('rental'):flags.append('租赁')
                    if item.get('perishable') is not None:flags.append('易腐 '+str(item['perishable']))
                    if item.get('edition'):flags.append(ED.get(item['edition'],item['edition']))
                    if item.get('debuff') or item.get('debuff_round'):flags.append('禁用')
                    if flags:desc+=' ['+', '.join(flags)+']'
                    if g.boss_active('Amber Acorn'):
                        name='??';desc='背面朝上的小丑牌' if self.language.startswith('zh_') else 'Face-down Joker'
                    title=f'♛  Joker {idx+1:>2}  ·  '+name
                else:
                    item=g.consumables[idx]
                    title=f'✦  消耗牌 {idx+1:>2}  ·  '+name_item(item['type'],item['name'])
                    desc=self.pack_brief(item,g)
                c.put(boxx+4,yy+1,cut(title,boxw-8),BLUE if focused else INK,bg2,focused)
                # Same lower-edge caption layout as shop and pack outlines.
                c.put(boxx+4,yy+2,' '+cut(desc,boxw-11)+' ',CYAN if focused else DIM,bg2)
            c.centered(ax,y+H-12,cw,('Joker 排序中：W/S 调换顺序 · M 完成' if self.inventory_reorder else '↑↓/WS 选择 · Enter 使用效果牌 · E 详情 · M Joker 排序'),CYAN,bg)
        c.centered(ax,y+H-9,cw,('←→ / AD 翻页    Enter 使用效果牌 · Backspace 出售 Joker · I / Esc 返回' if self.language.startswith('zh_') else 'A/D: page · Enter: use consumable · Backspace: sell Joker · I/Esc: back'),DIM,bg)

    def _detail_page(self,c,x,y,W,H,bg,g):
        from .explain import item_description,joker_description,card_description,explain_effect,voucher_description
        d=self.detail or {}
        typ=d.get('kind','');idx=d.get('index',0)
        title='牌  面  说  明';lines=[]
        try:
            if typ=='hand' and g:
                card=g.hand[idx];title=f'手牌  {idx+1}  ·  {card.rank}{card.suit}';lines=card_description(card)
            elif typ=='joker' and g:
                j=g.jokers[idx];o=LOOKUP[j['name']];title=f'小丑牌  {idx+1}  ·  {o.zh}';lines=joker_description(j['name'],g,j)
            elif typ=='shop' and g:
                item=g.shop[idx];title=f'商店商品  {idx+1}  ·  '+name_item(item['type'],item['name']);lines=item_description(item,g)+['当前商店售价：$'+str(item['cost'])]
            elif typ=='pack_info' and g and g.state=='shop':
                pack=g.packs[idx]
                title='商店补充包  ·  '+{'Normal':'普通','Jumbo':'大型','Mega':'巨型'}[pack['size']]+PACK_KINDS[pack['kind']]
                from .content import PACK_CONFIG,PACK_SIZES
                shown=PACK_CONFIG[pack['kind']][0 if pack['size']=='Normal' else 1]
                picks=PACK_SIZES[pack['size']][1]
                lines=['补充包类别：'+PACK_KINDS[pack['kind']],
                       f'共提供 {shown} 个候选奖励；可以选择 {picks} 个。',
                       '购买后会进入独立选择页面，奖励不会在每次选择后重新补入。',
                       f'售价：${pack["cost"]}；当前金币：${g.money}',
                       '打开前可先查看奖励类别。具体候选奖励在购买后生成。']
            elif typ=='pack' and g and g.pack:
                item=g.pack['options'][idx];title=f'补充包  {idx+1}  ·  '+name_item(item['type'],item['name']);lines=item_description(item,g)
            elif typ=='consumable' and g:
                item=g.consumables[idx];title=f'持有消耗牌  {idx+1}  ·  '+name_item(item['type'],item['name']);lines=item_description(item,g)
            elif typ=='voucher' and g and g.shop_voucher:
                title='当前商店优惠券';lines=voucher_description(g.shop_voucher)
            elif typ=='effect':
                from .explain import EFFECT_GROUPS
                gg=d.get('group',0);title='效果图鉴  ·  '+EFFECT_GROUPS[gg][0];lines=explain_effect(gg,idx,g)
            elif typ=='gallery':
                j=JOKERS[idx];title='小丑图鉴  ·  '+j.zh;lines=joker_description(j.name,g)
        except (IndexError,TypeError,KeyError,AttributeError) as exc:
            lines=['此卡目前不在当前页面或已经变动。','返回页面后重新打开。']
        if not self.language.startswith('zh_'):
            from .content_en import description,ENHANCEMENT_EN,EDITION_EN,SEAL_EN
            if typ=='joker' and g and 0<=idx<len(g.jokers):
                item=g.jokers[idx];key=item['name'];obj=LOOKUP.get(key)
                title=f'Joker {idx+1} · {key}'
                lines=[f'Rarity: {obj.rarity if obj else "Unknown"} · Cost: ${obj.cost if obj else 0}',
                       'Effect: '+description('Joker',key),
                       f'Sell value: ${item.get("sell",0)}']
            elif typ=='gallery' and 0<=idx<len(JOKERS):
                key=JOKERS[idx].name;title='Joker collection · '+key
                lines=['Effect: '+description('Joker',key)]
            elif typ in ('shop','pack','consumable') and g:
                opts=g.shop if typ=='shop' else g.pack['options'] if typ=='pack' and g.pack else g.consumables
                if 0<=idx<len(opts):
                    item=opts[idx];key=item['name'];cardtyp=item['type']
                    title=cardtyp+' · '+key
                    lines=['Effect: '+description(cardtyp,key)]
                    if typ=='shop':lines.append(f'Price: ${item["cost"]}')
            elif typ=='hand' and g and 0<=idx<len(g.hand):
                card=g.hand[idx];title=f'Hand card {idx+1} · {card.rank}{card.suit}'
                lines=[f'Rank chips: {card.chips()} · Bonus chips: {card.bonus}',
                       'Enhancement: '+(description('Enhancement',card.enhancement) if card.enhancement else 'None'),
                       'Edition: '+(description('Edition',card.edition) if card.edition else 'None'),
                       'Seal: '+(description('Seal',card.seal) if card.seal else 'None')]
            elif typ=='pack_info' and g and 0<=idx<len(g.packs):
                item=g.packs[idx];title=item['kind']+' Pack'
                lines=[f'Choose rewards from a {item["size"]} pack.',f'Price: ${item["cost"]}',
                       'Selected cards are removed; no replacement candidates appear.']
            elif typ=='voucher' and g and g.shop_voucher:
                title='Voucher · '+g.shop_voucher
                lines=['A permanent upgrade for this run.',
                       'A purchased voucher cannot appear again.']
            elif typ=='effect':
                from .explain import EFFECT_GROUPS
                gg=d.get('group',0)
                if 0<=gg<len(EFFECT_GROUPS) and 0<=idx<len(EFFECT_GROUPS[gg][1]):
                    item=EFFECT_GROUPS[gg][1][idx]
                    title=item['type']+' · '+item['name']
                    lines=['Effect: '+description(item['type'],item['name'])]
        c.centered(x+8,y+7,W-16,'✦   '+cut(title,W-20)+'   ✦',GOLD,bg,True)
        px=x+max(8,(W-min(W-16,108))//2);pw=min(W-16,108)
        ph=min(H-19,39)
        c.box(px,y+11,pw,ph,BLUE,bg)
        yy=y+14
        for i,txt in enumerate(lines):
            if yy>=y+11+ph-4:break
            if i:c.hline(px+5,yy,pw-10,BORDER,'─',bg);yy+=1
            size=self._text_lines(c,px+6,yy,pw-12,txt,bg,INK if i else CYAN,3)
            yy+=size+2
        c.centered(x+8,y+H-10,W-16,'E / Enter / Esc 关闭说明页，继续之前的操作',DIM,bg)

    def _effects_page(self,c,x,y,W,H,bg,g):
        from .explain import EFFECT_GROUPS
        group=self.effects_group%len(EFFECT_GROUPS)
        label,data=EFFECT_GROUPS[group]
        if not self.language.startswith('zh_'):
            label=['Tarot','Planet','Spectral','Enhancements','Editions','Seals','Vouchers'][group]
        per_page=8
        self.effects_cursor=max(0,min(len(data)-1,self.effects_cursor))
        pages=max(1,math.ceil(len(data)/per_page));self.effects_page=self.effects_cursor//per_page
        c.centered(x+8,y+7,W-16,'✦  效 果 牌 图 鉴  ✦',GOLD,bg,True)
        c.centered(x+8,y+9,W-16,('←→ / AD 切换类别  │  ↑↓ / WS 选牌/翻页  │  E 查看当前焦点详情' if self.language.startswith('zh_') else 'A/D: category · W/S: select and scroll · E: details'),DIM,bg)
        labels=[x[0] for x in EFFECT_GROUPS] if self.language.startswith('zh_') else ['Tarot','Planet','Spectral','Enhancements','Editions','Seals','Vouchers']
        gnames='  /  '.join(('【'+name+'】' if i==group else name) for i,name in enumerate(labels))
        c.centered(x+6,y+12,W-12,cut(gnames,W-16),CYAN,bg)
        c.centered(x+8,y+15,W-16,f'{label}   ·   {self.effects_page+1} / {pages}',GOLD,bg,True)
        start=self.effects_page*per_page
        ax=x+max(9,(W-112)//2)
        for i,item in enumerate(data[start:start+per_page],start+1):
            yy=y+18+(i-start-1)*2
            typ,n=item['type'],item['name']
            if typ=='Tarot':name=TAROT_ZH[n] if self.language.startswith('zh_') else n
            elif typ=='Planet':name=PLANET_ZH[n] if self.language.startswith('zh_') else __import__('arcana.poker',fromlist=['PLANETS']).PLANETS[n]
            elif typ=='Spectral':name=SPECTRAL_ZH[n] if self.language.startswith('zh_') else n
            elif typ=='Enhancement':name=ENH.get(n,n) if self.language.startswith('zh_') else n
            elif typ=='Edition':name=ED.get(n,n) if self.language.startswith('zh_') else n
            elif typ=='Seal':name=SEAL.get(n,n) if self.language.startswith('zh_') else n
            else:name=VOUCHERS[n]['desc'][:16] if self.language.startswith('zh_') else n
            chosen=(i-1)==self.effects_cursor
            c.put(ax,yy,('➤' if chosen else '·')+f' {i:>2}. '+cut(name,24),BLUE if chosen else GOLD,bg,True)
            if typ in ('Tarot','Planet','Spectral'):
                from .explain import item_description
                desc=item_description(item,g)[1] if typ!='Planet' else item_description(item,g)[2]
            elif typ=='Voucher':desc=VOUCHERS[n]['desc']
            else:
                from .explain import ENH_DETAIL,ED_DETAIL,SEAL_DETAIL
                desc=(ENH_DETAIL[n][1] if typ=='Enhancement' else ED_DETAIL[n] if typ=='Edition' else SEAL_DETAIL[n])
            if not self.language.startswith('zh_'):desc=english_card_description(typ,n)
            c.put(ax+31,yy,cut(desc,min(70,W-56)),BLUE if chosen else INK,bg)
        c.centered(x+7,y+H-10,W-14,('W/S 选中任意卡牌后按 E 查看详情；切换到下一页会自动滚动' if self.language.startswith('zh_') else 'W/S: select a card · E: details · page scrolls automatically'),DIM,bg)

class RawTerminal:
    """Read single keypresses without echoing them; restore the previous terminal.

    Windows uses msvcrt + Win32 output mode; macOS keeps the POSIX cbreak
    implementation unchanged. No pip dependencies or platform-specific UI fork.
    """
    def __enter__(self):
        self.pending = ''
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.GetStdHandle.argtypes = [wintypes.DWORD]
            kernel.GetStdHandle.restype = wintypes.HANDLE
            kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            kernel.GetConsoleMode.restype = wintypes.BOOL
            kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel.SetConsoleMode.restype = wintypes.BOOL
            self._kernel = kernel
            self._h = kernel.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            oldmode = wintypes.DWORD()
            if not kernel.GetConsoleMode(self._h, ctypes.byref(oldmode)):
                raise RuntimeError('无法读取 Windows 控制台模式；请在 Windows Terminal 里运行。')
            self._oldmode = oldmode.value
            # ENABLE_PROCESSED_OUTPUT, ENABLE_VIRTUAL_TERMINAL_PROCESSING,
            # DISABLE_NEWLINE_AUTO_RETURN. Older consoles may reject the last.
            mode = self._oldmode | 0x0001 | 0x0004 | 0x0008
            if not kernel.SetConsoleMode(self._h, mode):
                mode &= ~0x0008
                if not kernel.SetConsoleMode(self._h, mode):
                    raise RuntimeError('终端不支持 ANSI 彩色绘制；请使用新版 Windows Terminal。')
        else:
            self.fd = sys.stdin.fileno()
            self.old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        try:
            sys.stdout.write('\033[?1049h\033[?25l\033[0m\033[2J')
            sys.stdout.flush()
        except BaseException:
            # A failed first draw must not leave the console in VT-only mode.
            if os.name == 'nt':
                self._kernel.SetConsoleMode(self._h, self._oldmode)
            else:
                termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
            raise
        return self

    def __exit__(self, *args):
        # Important on Windows: the exit escape must be processed while VT
        # processing is still enabled; restore the original mode afterwards.
        try:
            sys.stdout.write('\033[0m\033[?25h\033[?1049l')
            sys.stdout.flush()
        finally:
            if os.name == 'nt':
                self._kernel.SetConsoleMode(self._h, self._oldmode)
            else:
                termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)

    def read(self):
        if os.name == 'nt':
            # msvcrt.getwch returns a UTF-16 key; navigation keys are prefixed
            # with 0x00/0xe0, so a second read produces the scan code.
            first = msvcrt.getwch()
            if first in ('\x00', '\xe0'):
                code = msvcrt.getwch()
                key = {'H':'UP', 'P':'DOWN', 'K':'LEFT', 'M':'RIGHT'}.get(code)
                return [key] if key else []
            if first in ('\r','\n'): return ['ENTER']
            if first in ('\x08','\x7f'): return ['BACKSPACE']
            if first == '\x03': return ['CTRL_C']
            if first == '\x1b': return ['ESC']
            return [first] if ord(first) >= 32 else []
        data=os.read(self.fd,128).decode('utf-8','ignore')
        self.pending+=data
        result=[]
        while self.pending:
            v=self.pending
            if v.startswith('\x1b['):
                if len(v)<3:
                    if select.select([self.fd],[],[],.03)[0]:self.pending+=os.read(self.fd,64).decode('utf8','ignore');continue
                    result.append('ESC');self.pending=self.pending[1:];continue
                if v[2] in 'ABCD':
                    result.append({'A':'UP','B':'DOWN','C':'RIGHT','D':'LEFT'}[v[2]])
                    self.pending=v[3:];continue
                result.append('ESC');self.pending=v[1:];continue
            if v[0]=='\x1b':
                if len(v)==1 and select.select([self.fd],[],[],.03)[0]:
                    self.pending+=os.read(self.fd,64).decode('utf8','ignore');continue
                result.append('ESC')
            elif v[0] in ('\r','\n'):result.append('ENTER')
            elif v[0] in ('\x7f','\b'):result.append('BACKSPACE')
            elif v[0]=='\x03':result.append('CTRL_C')
            elif ord(v[0])>=32:result.append(v[0])
            self.pending=v[1:]
        return result
