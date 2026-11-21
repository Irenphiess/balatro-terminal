#!/usr/bin/env python3
"""Balatro — macOS / Windows terminal edition with multilingual UI and scene soundtrack."""
from __future__ import annotations
import argparse,sys,os
from arcana.game import Game
from arcana.tui import UI,RawTerminal,DECKS,STAKES
from arcana.music import Music,resize_terminal
from arcana.i18n import LANGUAGES,save_language,load_language,tr,localize_event


class Controller:
    def __init__(self,music=None,language='zh_CN'):
        self.ui=UI(language=language);self.game=None;self.music=music
        self.update_audio()
    def music_scene(self):
        g=self.game
        if g is None:return 'title'
        if g.state=='shop':return 'shop'
        if g.state=='pack':
            kind=(g.pack or {}).get('kind','Standard')
            if kind=='Celestial':return 'celestial'
            if kind in ('Arcana','Spectral'):return 'arcana'
            return 'play'
        if g.blind==2 and g.state in ('blind','play'):return 'boss'
        return 'play'
    def shop_current(self):
        g=self.game;u=self.ui
        if not g or g.state!='shop':raise ValueError('当前不在商店')
        entries=u.shop_entries(g)
        if not entries:raise ValueError('商店已售完。按 N 进入下一轮')
        u.cursor_shop=max(0,min(u.cursor_shop,len(entries)-1))
        return entries[u.cursor_shop]
    def shop_confirm(self):
        typ,index=self.shop_current();g=self.game
        if typ=='owned_joker':g.sell_joker(index)
        elif typ=='owned_consumable':
            self.use_consumable(index,return_overlay=None)
            return
        elif typ=='card':g.buy(index)
        elif typ=='pack':g.open_pack(index)
        else:g.buy_voucher()
        self.ui.cursor_shop=min(self.ui.cursor_shop,max(0,len(self.ui.shop_entries(g))-1))
        self.note(g.log[-1] if g.log else '购买成功')
        self.stash()
    def shop_explain(self):
        typ,index=self.shop_current()
        self.ui.detail={'kind':{'owned_joker':'joker','owned_consumable':'consumable','card':'shop','pack':'pack_info','voucher':'voucher'}[typ], 'index':index}
        self.ui.detail_return=None;self.ui.overlay='detail'
    def update_audio(self):
        self.ui.music_available=bool(self.music and self.music.available)
        self.ui.music_enabled=bool(self.music and self.music.enabled)
    def note(self,msg):self.ui.message=localize_event(msg,self.ui.language)
    def stash(self):
        if self.game and self.game.state!='lost':
            self.game.save()
    def load(self,path=None):
        self.game=Game.load(path)
        u=self.ui;u.stage='select';u.cursor_shop=0;u.cursor_pack=0;u.pending_pack_index=None;u.target_indices=[];u.overlay=None;u.detail=None;u.inventory_page=0;u.inventory_joker_cursor=0;u.inventory_cursor=0;u.inventory_deck_scroll=0;u.inventory_reorder=False;u.pending_use_index=None;u.use_return=None;u.focus='hand';u.cursor_hand=0;u.cursor_joker=0;u.selected_uids=[];u.command=''
        self.note(f'存档已恢复 · Ante {self.game.ante} / {self.game.blind_name()} / {self.game.state}')
    def confirm(self):
        u=self.ui;g=self.game
        if u.overlay:
            u.overlay=u.detail_return if u.overlay=='detail' else None
            u.detail_return=None;u.detail=None
            return
        if g is None:
            if u.stage=='splash':u.stage='select';self.note('选择牌组与难度，按 Enter 创建新游戏');return
            d=DECKS[u.deck_index];stake=STAKES[u.stake_index]
            self.game=Game.new_run(d.key,stake[0]);u.selected_uids=[]
            self.note(f'新游戏 · {d.name} / {stake[1]} · Enter 开始盲注')
            self.stash()
        elif g.state=='blind':
            g.start_blind()
            if g.boss_active('Cerulean Bell') and g.locked_card:
                u.selected_uids=[g.locked_card]
            self.note(g.log[-1]);self.stash()
        elif g.state=='shop':self.shop_confirm()
        elif g.state=='lost':
            self.game=None;u.overlay=None;u.stage='splash';self.note('按 Enter 返回牌组选择之前的封面')
        elif g.state=='pack':self.pack_confirm()
        elif g.state=='play':
            if u.focus=='joker' and g.jokers:
                u.detail={'kind':'joker','index':min(u.cursor_joker,len(g.jokers)-1)};u.overlay='detail'
                return
            if not g.hand:return
            uid=g.hand[min(u.cursor_hand,len(g.hand)-1)].uid
            if uid in u.selected_uids:
                if uid==g.locked_card and g.boss_active('Cerulean Bell'):
                    self.note('蔚蓝铃铛：此牌必须被选中，不可取消')
                    return
                u.selected_uids.remove(uid)
            elif len(u.selected_uids)<5:u.selected_uids.append(uid)
            else:raise ValueError('最多选中 5 张手牌')
            self.note(f'已选 {len(u.selected_uids)} 张：P 出牌 / O 弃牌')
    @staticmethod
    def pack_target_bounds(item):
        if item['type']=='Tarot':
            name=item['name']
            if name=='Death':return 2,2
            if name in ('The Star','The Moon','The Sun','The World'):return 1,3
            if name in ('The Hanged Man','Strength','The Magician','The Empress','The Hierophant'):return 1,2
            if name in ('The Lovers','The Chariot','Justice','The Devil','The Tower'):return 1,1
        if item['type']=='Spectral' and item['name'] in ('Aura','Talisman','Deja Vu','Trance','Medium','Cryptid'):
            return 1,1
        return 0,0
    def pack_confirm(self):
        g=self.game;u=self.ui
        if not g or g.state!='pack' or not g.pack:raise ValueError('当前没有补充包')
        u.cursor_pack=max(0,min(u.cursor_pack,len(g.pack['options'])-1))
        index=u.cursor_pack;item=g.pack['options'][index]
        low,high=self.pack_target_bounds(item)
        if low:
            if not g.hand:raise ValueError('此效果需要手牌，但当前没有可选目标')
            u.overlay='pack_target';u.pending_pack_index=index
            u.target_cursor=0;u.target_indices=[]
            u.target_min=low;u.target_max=min(high,len(g.hand))
            if u.target_max<low:raise ValueError('目标手牌数量不足')
            self.note('请选择目标手牌：←→ 移动 / Enter 选中 / P 确认')
            return
        self.pack_pick(index,[])
    def use_consumable(self,index,return_overlay='hand'):
        """Use an equipped effect card via UI; target selection is a separate full page."""
        g=self.game;u=self.ui
        if g is None or not 0<=index<len(g.consumables):
            raise ValueError('这张效果牌已不存在')
        item=g.consumables[index]
        low,high=self.pack_target_bounds(item)
        if low:
            if not g.hand:raise ValueError('此牌需要指定手牌：当前没有可选手牌')
            u.overlay='use_target';u.pending_use_index=index;u.use_return=return_overlay
            u.target_cursor=0;u.target_indices=[];u.target_min=low;u.target_max=min(high,len(g.hand))
            if u.target_max<low:raise ValueError('可选目标数量不足')
            self.note('选择效果牌目标：A/D 移动 · Enter 选中 · P 确认 · Esc 返回')
            return
        self.complete_use(index,[],return_overlay)

    def complete_use(self,index,targets,return_overlay='hand'):
        g=self.game;u=self.ui
        before=g.consumables[index]['name']
        g.use(index,targets)
        u.overlay=return_overlay;u.pending_use_index=None;u.target_indices=[]
        u.inventory_page=min(u.inventory_page,u.inventory_pages(g)-1)
        u.inventory_cursor=min(u.inventory_cursor,max(0,len(u.inventory_page_entries(g))-1))
        u.cursor_shop=min(u.cursor_shop,max(0,len(u.shop_entries(g))-1))
        self.note('已使用效果牌：'+before)
        self.stash()

    def use_target_commit(self):
        u=self.ui
        if len(u.target_indices)<u.target_min:
            raise ValueError(f'至少选择 {u.target_min} 张目标手牌')
        self.complete_use(u.pending_use_index,list(u.target_indices),u.use_return)

    def use_target_toggle(self):
        u=self.ui
        i=u.target_cursor
        if i in u.target_indices:u.target_indices.remove(i)
        elif len(u.target_indices)<u.target_max:u.target_indices.append(i)
        else:raise ValueError(f'最多选择 {u.target_max} 张目标')
        if len(u.target_indices)==u.target_max and u.target_max==u.target_min:
            self.use_target_commit()
        else:self.note(f'已选目标 {len(u.target_indices)} / {u.target_max}；P 确认使用')

    def move_inventory_joker(self,step):
        u=self.ui;g=self.game
        entries=u.inventory_page_entries(g)
        if not entries or not 0<=u.inventory_cursor<len(entries):return
        typ,index=entries[u.inventory_cursor]
        if typ!='joker':return
        target=index+step
        if not 0<=target<len(g.jokers):return
        g.jokers[index],g.jokers[target]=g.jokers[target],g.jokers[index]
        u.inventory_page=target//u.inventory_capacity()
        u.inventory_cursor=target%u.inventory_capacity()
        self.note('已调整 Joker 次序（左右结算顺序会影响分数）')
        self.stash()

    def pack_pick(self,index,targets):
        g=self.game;u=self.ui
        g.select_pack(index,targets)
        u.cursor_pack=min(index,max(0,len(g.pack['options'])-1)) if g.pack else 0
        u.pending_pack_index=None;u.target_indices=[];u.overlay=None
        self.note(g.log[-1] if g.log else '已选择奖励')
        if g.state=='shop':u.cursor_shop=min(u.cursor_shop,max(0,len(u.shop_entries(g))-1))
        self.stash()
    def pack_target_toggle(self):
        u=self.ui;g=self.game
        i=u.target_cursor
        if i in u.target_indices:u.target_indices.remove(i)
        elif len(u.target_indices)<u.target_max:u.target_indices.append(i)
        else:raise ValueError(f'最多选择 {u.target_max} 张目标手牌')
        if len(u.target_indices)==u.target_max and u.target_min==u.target_max:
            self.pack_target_commit()
        else:self.note(f'目标：{len(u.target_indices)}/{u.target_max}，P 确认应用')
    def pack_target_commit(self):
        u=self.ui
        if len(u.target_indices)<u.target_min:raise ValueError(f'请至少选择 {u.target_min} 张目标手牌')
        self.pack_pick(u.pending_pack_index,list(u.target_indices))
    def execute(self,line):
        u=self.ui;g=self.game
        parts=line.strip().lower().split()
        if not parts:return
        op,*args=parts
        # All card selection and transactions now use the on-screen focus.
        # Numbered commands (with OR without spaces) are intentionally removed.
        if args:raise ValueError('请通过方向键 / WASD 和 Enter 在界面中操作，无须输入编号')
        if op in ('q','quit'):
            if g and g.state!='lost':g.save()
            u.quit=True;return
        if op in ('v','lang','language'):
            if u.overlay=='language':u.overlay=u.language_return;u.language_return=None
            else:
                u.language_return=u.overlay;u.overlay='language'
                u.language_cursor=next((i for i,(code,_) in enumerate(LANGUAGES) if code==u.language),0)
            return
        if op in ('h','help','?'):
            u.overlay=None if u.overlay=='help' else 'help';u.help_page=0;return
        if op in ('g','gallery'):u.overlay=None if u.overlay=='gallery' else 'gallery';u.page=0;u.gallery_cursor=0;return
        if op in ('f','effects'):u.overlay=None if u.overlay=='effects' else 'effects';u.effects_page=0;u.effects_cursor=0;return
        if op=='e' and u.overlay=='detail' and not args:
            u.overlay=u.detail_return;u.detail_return=None;u.detail=None;return
        if op=='e' and g and g.state=='shop' and not args:self.shop_explain();return
        if op=='e' and g and g.state=='pack' and not args:
            if not g.pack or not g.pack['options']:raise ValueError('当前没有奖励可以查看')
            u.cursor_pack=max(0,min(u.cursor_pack,len(g.pack['options'])-1))
            u.detail={'kind':'pack','index':u.cursor_pack};u.overlay='detail';u.detail_return=None;return
        if op=='c':
            if not self.music or not self.music.available:
                self.note('当前环境没有可用的系统音频播放器')
            else:
                self.music.toggle();self.update_audio();self.note('背景音乐已'+('开启' if self.music.enabled else '关闭'))
            return
        if op=='l':self.load();return
        if op=='i' and g:
            if u.overlay=='hand':u.overlay=None
            else:u.overlay='hand';u.inventory_page=0;u.inventory_cursor=0;u.inventory_deck_scroll=0
            return
        if op=='x' and g:u.overlay=None if u.overlay=='levels' else 'levels';return
        if op=='k' and g:g.save();self.note('已保存：'+str(Game.save_candidates()[0]));return
        if op=='y' and g and g.state=='lost':self.confirm();return
        if op in ('enter','start') and not args:self.confirm();return
        if g is None:raise ValueError('WASD 选择牌组，方向键选择难度；Enter 开始，L 继续存档')
        if op=='t':g.skip_blind()
        elif op=='e' and not args and g.state=='blind':g.reroll_boss()
        elif op in ('p','o'):
            if g.state=='play' and op=='p' and g.boss_active('Cerulean Bell') and g.locked_card:
                if g.locked_card not in u.selected_uids:u.selected_uids.append(g.locked_card)
            ids=[i for i,z in enumerate(g.hand) if z.uid in u.selected_uids]
            if not ids:raise ValueError('请先用左右键与 Enter 选中要出牌/弃掉的手牌')
            if op=='p':g.play(ids)
            else:g.discard(ids)
            u.selected_uids=[];u.cursor_hand=0;u.focus='hand'
            if op=='p' and g.state=='play' and g.boss_active('Cerulean Bell') and g.locked_card:
                u.selected_uids=[g.locked_card]
        elif op=='z':g.skip_pack()
        elif op=='r':g.reroll()
        elif op=='m':raise ValueError('请在 I 持有 Joker 界面按 M 启用排序模式，再用 W/S 调整顺序')
        elif op=='n':g.next_blind()
        else:raise ValueError('无效指令：H 查看帮助')
        if g.log:self.note(g.log[-1])
        if g.state=='shop' and op in ('p','o','n'):u.cursor_shop=0
        if g.state=='lost':self.note('挑战失败。Enter 返回开屏，可按 L 重读先前存档')
        if u.overlay not in ('gallery','help','levels','effects'):
            if op!='i':u.overlay=None
        self.stash()
    def key(self,k):
        u=self.ui;g=self.game
        if k=='CTRL_C':u.quit=True;return
        # Directional input has a single meaning in EVERY navigable screen.
        # Only the initial deck/stake setup deliberately distinguishes WASD
        # (decks) from real arrow keys (stakes). A pending text command disables
        # WASD translation until the command is submitted or cleared.
        if not u.command and not (g is None and u.stage=='select' and u.overlay is None):
            k={'w':'UP','s':'DOWN','a':'LEFT','d':'RIGHT'}.get(k.lower(),k) if isinstance(k,str) and len(k)==1 else k
        if k=='ESC':
            if u.command:u.command=''
            elif u.overlay=='language':
                u.overlay=u.language_return;u.language_return=None
            elif u.overlay=='use_target':
                u.overlay=u.use_return;u.pending_use_index=None;u.target_indices=[]
                self.note('已取消使用，未消耗效果牌')
            elif u.overlay=='pack_target':
                u.overlay=None;u.pending_pack_index=None;u.target_indices=[]
                self.note('取消目标选择，返回补充包')
            elif g is None and u.stage=='select':u.stage='splash'
            else:
                u.overlay=u.detail_return if u.overlay=='detail' else None
                u.detail_return=None;u.detail=None
            return
        if k in ('v','V') and not u.command and u.overlay!='language':
            self.execute('v');return
        if u.overlay=='language':
            if k in ('UP','DOWN'):
                u.language_cursor=(u.language_cursor+(-1 if k=='UP' else 1))%len(LANGUAGES)
            elif k=='ENTER':
                code,_=LANGUAGES[u.language_cursor]
                u.language=code
                try:save_language(code)
                except OSError:self.note('语言已切换，但设置文件未能保存')
                else:self.note(tr('language_saved',code)+' · '+dict(LANGUAGES)[code])
                u.overlay=u.language_return;u.language_return=None
            elif k in ('v','V'):
                u.overlay=u.language_return;u.language_return=None
            return
        if u.command and k in ('UP','DOWN','LEFT','RIGHT'):
            # Command editing is modal: neither input method navigates mid-command.
            return
        if u.overlay=='use_target':
            if k in ('LEFT','RIGHT') and g and g.hand:
                u.target_cursor=(u.target_cursor+(-1 if k=='LEFT' else 1))%len(g.hand)
            elif k=='ENTER':
                try:self.use_target_toggle()
                except (ValueError,IndexError,KeyError,TypeError) as exc:self.note('未应用：'+str(exc))
            elif k in ('p','P'):
                try:self.use_target_commit()
                except (ValueError,IndexError,KeyError,TypeError) as exc:self.note('未应用：'+str(exc))
            return
        if u.overlay=='pack_target':
            if k in ('LEFT','RIGHT') and g and g.hand:
                u.target_cursor=(u.target_cursor+(-1 if k=='LEFT' else 1))%len(g.hand)
            elif k=='ENTER':
                try:self.pack_target_toggle()
                except (ValueError,IndexError,KeyError,TypeError) as exc:self.note('目标未选：'+str(exc))
            elif k in ('p','P'):
                try:self.pack_target_commit()
                except (ValueError,IndexError,KeyError,TypeError) as exc:self.note('尚不能应用：'+str(exc))
            return
        if u.overlay=='detail':
            if k in ('ENTER','ESC','e','E','h','H'):
                u.overlay=u.detail_return;u.detail_return=None;u.detail=None
            return
        if u.overlay=='gallery':
            from arcana.content import JOKERS
            if k in ('RIGHT','LEFT'):
                max_page=(len(JOKERS)-1)//12
                u.page=max(0,min(max_page,u.page+(1 if k=='RIGHT' else -1)))
                u.gallery_cursor=0;return
            if k in ('UP','DOWN'):
                number=len(JOKERS[u.page*12:(u.page+1)*12])
                if number:u.gallery_cursor=(u.gallery_cursor+(-1 if k=='UP' else 1))%number
                return
            if k in ('e','E'):
                index=u.page*12+u.gallery_cursor
                if index<len(JOKERS):
                    u.detail={'kind':'gallery','index':index};u.detail_return='gallery';u.overlay='detail'
                return
            if k in ('ENTER','g','G'):u.overlay=None
            return
        if u.overlay=='effects':
            from arcana.explain import EFFECT_GROUPS
            if k in ('LEFT','RIGHT'):
                u.effects_group=(u.effects_group+(-1 if k=='LEFT' else 1))%len(EFFECT_GROUPS)
                u.effects_cursor=0;u.effects_page=0;return
            if k in ('UP','DOWN'):
                number=len(EFFECT_GROUPS[u.effects_group][1])
                if number:u.effects_cursor=(u.effects_cursor+(-1 if k=='UP' else 1))%number
                u.effects_page=u.effects_cursor//8;return
            if k in ('e','E'):
                u.detail={'kind':'effect','index':u.effects_cursor,'group':u.effects_group}
                u.detail_return='effects';u.overlay='detail';return
            if k in ('ENTER','f','F'):u.overlay=None
            return
        if u.overlay=='help':
            if k in ('LEFT','RIGHT'):
                u.help_page=max(0,u.help_page+(-1 if k=='LEFT' else 1));return
            if k in ('ENTER','h','H'):u.overlay=None
            return
        if u.overlay=='levels':
            if k in ('ENTER','x','X'):u.overlay=None
            return
        if u.overlay=='hand':
            pages=u.inventory_pages(g)
            if k=='BACKSPACE':
                if not g or u.inventory_is_deck(g):
                    self.note('请切换至 Joker 持有页后选择要出售的牌')
                    return
                entries=u.inventory_page_entries(g)
                if not entries:
                    self.note('当前没有可以出售的 Joker')
                    return
                typ,index=entries[min(u.inventory_cursor,len(entries)-1)]
                if typ!='joker':
                    self.note('请先选中 Joker；Backspace 才会出售它')
                    return
                try:
                    sold=g.jokers[index]['name']
                    g.sell_joker(index)
                    u.inventory_reorder=False
                    u.inventory_page=min(u.inventory_page,u.inventory_pages(g)-1)
                    u.inventory_cursor=min(u.inventory_cursor,max(0,len(u.inventory_page_entries(g))-1))
                    self.note('已出售 Joker：'+sold)
                    self.stash()
                except (ValueError,IndexError,KeyError,TypeError) as exc:
                    self.note('出售失败：'+str(exc))
                return
            if k in ('m','M'):
                if u.inventory_is_deck(g):
                    self.note('牌组页不能调整 Joker，请翻回持有牌页')
                else:
                    entries=u.inventory_page_entries(g)
                    if entries and entries[min(u.inventory_cursor,len(entries)-1)][0]=='joker':
                        u.inventory_reorder=not u.inventory_reorder
                        self.note('Joker 排序模式：W/S 移动小丑，M 完成' if u.inventory_reorder else '已完成 Joker 排序')
                    else:self.note('请先选中一张 Joker 再按 M 调整排序')
                return
            if k in ('LEFT','RIGHT'):
                u.inventory_reorder=False
                u.inventory_page=max(0,min(pages-1,u.inventory_page+(-1 if k=='LEFT' else 1)))
                u.inventory_cursor=0;u.inventory_deck_scroll=0
            elif k in ('UP','DOWN'):
                if u.inventory_is_deck(g):
                    W=u.last_layout[2] if u.last_layout else 158
                    H=u.last_layout[3] if u.last_layout else 54
                    total=len(u.deck_visual_rows(g,W))
                    maximum=max(0,total-u.deck_visible_rows(H))
                    u.inventory_deck_scroll=max(0,min(maximum,u.inventory_deck_scroll+(-1 if k=='UP' else 1)))
                elif u.inventory_reorder:
                    try:self.move_inventory_joker(-1 if k=='UP' else 1)
                    except (ValueError,IndexError,KeyError,TypeError) as exc:self.note('排序未成功：'+str(exc))
                else:
                    entries=u.inventory_page_entries(g)
                    if entries:u.inventory_cursor=(u.inventory_cursor+(-1 if k=='UP' else 1))%len(entries)
            elif k in ('e','E') and not u.inventory_is_deck(g):
                entries=u.inventory_page_entries(g)
                if entries:
                    kind,index=entries[min(u.inventory_cursor,len(entries)-1)]
                    u.detail={'kind':kind,'index':index}
                    u.detail_return='hand';u.overlay='detail'
            elif k=='ENTER':
                if not u.inventory_is_deck(g):
                    entries=u.inventory_page_entries(g)
                    if entries:
                        typ,index=entries[min(u.inventory_cursor,len(entries)-1)]
                        if typ=='consumable':
                            try:self.use_consumable(index,return_overlay='hand')
                            except (ValueError,IndexError,KeyError,TypeError) as exc:self.note('效果未使用：'+str(exc))
                        else:self.note('Joker 已选中：E 详情 · M 调整结算顺序（Enter 不会关闭界面）')
            elif k in ('i','I'):
                u.overlay=None;u.inventory_reorder=False
            return
        if not u.command and g is None and u.stage=='select' and u.overlay is None:
            dirs={'a':-1,'d':1,'w':-5,'s':5}
            if isinstance(k,str) and k.lower() in dirs and len(k)==1:
                u.deck_index=(u.deck_index+dirs[k.lower()])%len(DECKS);return
            if k in ('LEFT','RIGHT','UP','DOWN'):
                delta={'LEFT':-1,'RIGHT':1,'UP':-4,'DOWN':4}[k]
                u.stake_index=(u.stake_index+delta)%len(STAKES);return
        if not u.command and g and g.state=='pack' and u.overlay is None:
            if k in ('UP','DOWN'):
                if g.pack and g.pack['options']:
                    u.cursor_pack=(u.cursor_pack+(-1 if k=='UP' else 1))%len(g.pack['options'])
                return
        if not u.command and g and g.state=='shop' and u.overlay is None:
            if k in ('UP','DOWN','LEFT','RIGHT','w','W','s','S','a','A','d','D'):
                count=len(u.shop_entries(g))
                if count:u.cursor_shop=(u.cursor_shop+(-1 if k in ('UP','LEFT','w','W','a','A') else 1))%count
                return
        if not u.command and g and g.state=='play' and u.overlay is None:
            if k in ('LEFT','RIGHT','a','A','d','D'):
                backward=k in ('LEFT','a','A')
                if u.focus=='hand' and g.hand:
                    u.cursor_hand=(u.cursor_hand+(-1 if backward else 1))%len(g.hand)
                elif u.focus=='joker' and g.jokers:
                    u.cursor_joker=(u.cursor_joker+(-1 if backward else 1))%len(g.jokers)
                return
            if k in ('UP','w','W'):
                if g.jokers:u.focus='joker'
                return
            if k in ('DOWN','s','S'):u.focus='hand';return
        if k=='BACKSPACE':u.command=u.command[:-1];return
        if k=='ENTER':
            line=u.command.strip();u.command=''
            if line:self._safe(line)
            else:
                try:self.confirm()
                except (ValueError,IndexError,KeyError,TypeError,FileNotFoundError,RuntimeError) as exc:self.note('未执行：'+str(exc))
            return
        if k in ('UP','DOWN','LEFT','RIGHT'):return
        if not isinstance(k,str) or len(k)!=1:return
        if not u.command:
            letter=k.lower()
            if g and g.state=='play' and letter=='e':
                self.note('牌局中按 ↑ 选 Joker、Enter 查看；手牌按 Enter 选牌')
                return
            shortcuts={'h','g','f','q','l','c','v'}
            if g is None:pass
            else:
                shortcuts|={'i','x','k'}
                if g.state=='blind':shortcuts|={'t','e'}
                elif g.state=='shop':shortcuts|={'r','e','n'}
                elif g.state=='pack':shortcuts|={'z','e'}
                elif g.state=='play':shortcuts|={'p','o'}
            if letter in shortcuts:
                self._safe(letter);return
        # UI-first controls: no legacy free-text or numbered-command entry.
        self.note('此键没有操作：请使用方向键 / WASD 和 Enter，按 H 查看帮助')
    def _safe(self,cmd):
        try:self.execute(cmd)
        except (ValueError,IndexError,KeyError,TypeError,AttributeError,FileNotFoundError,RuntimeError,OSError) as exc:
            self.note('操作未执行：'+str(exc))


def main(argv=None):
    parser=argparse.ArgumentParser(description='Balatro · macOS / Windows Terminal')
    parser.add_argument('--no-resize',action='store_true',help='不尝试调整终端窗口尺寸')
    parser.add_argument('--size',default='160x60',help='建议终端尺寸，如 160x60')
    parser.add_argument('--no-music',action='store_true',help='启动时关闭音乐')
    args=parser.parse_args(argv)
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print('请在 macOS Terminal / iTerm2 或 Windows Terminal 中运行：python play.py')
        return 2
    # UTF-8 also covers running via an existing Windows PowerShell tab, without
    # relying on run.bat's chcp command.
    if os.name=='nt':
        for stream in (sys.stdout,sys.stderr):
            if hasattr(stream,'reconfigure'):
                stream.reconfigure(encoding='utf-8',errors='replace')
    requested_size = None
    if not args.no_resize:
        try:
            cols,rows=map(int,args.size.lower().split('x'))
            requested_size=(cols,rows)
        except (ValueError,AttributeError):pass
    # macOS resize occurs in exactly the same place as V13. On Windows the
    # escape must wait until the console has VT processing enabled below.
    if requested_size and os.name!='nt':resize_terminal(*requested_size)
    music=Music(enabled=not args.no_music);music.start()
    control=Controller(music,language=load_language())
    try:
        with RawTerminal() as term:
            if requested_size and os.name=='nt':resize_terminal(*requested_size)
            music.set_scene(control.music_scene())
            control.ui.draw(control.game)
            while not control.ui.quit:
                for k in term.read():
                    control.key(k)
                    if control.ui.quit:break
                if not control.ui.quit:
                    music.set_scene(control.music_scene())
                    control.ui.draw(control.game)
    finally:music.stop()
    return 0

if __name__=='__main__':sys.exit(main())
