"""Centered, large Chinese ANSI terminal UI. No non-standard dependencies."""
import os,re,sys,shutil,unicodedata
from .content import LOOKUP,JOKERS,TAROT_ZH,SPECTRAL_ZH,BOSS_ZH,BOSSES,PACK_KINDS,VOUCHERS
from .poker import HAND_ZH,PLANET_ZH,HANDS

ESC=re.compile(r'\x1b\[[0-9;]*m')
RESET='\x1b[0m'
def fg(r,g,b):return f'\x1b[38;2;{r};{g};{b}m'
def bg(r,g,b):return f'\x1b[48;2;{r};{g};{b}m'
GOLD=fg(250,200,109);AQUA=fg(88,222,224);GREEN=fg(126,224,148);MUTED=fg(146,166,181);WHITE=fg(242,245,248);RED=fg(246,105,110);ORANGE=fg(255,160,53);BLUE=fg(109,163,246);MAGENTA=fg(209,137,246)
BG=bg(17,26,40)
CARD_BG=bg(249,245,232)
CARD_EDGE=fg(93,106,124)
BLACK=fg(10,12,18)
SUIT_COLOR={'♥':fg(223,46,69),'♦':fg(243,137,27),'♠':fg(9,9,13),'♣':fg(29,137,77)}
RANK_COLOR={'♥':fg(194,32,55),'♦':fg(194,32,55),'♠':BLACK,'♣':BLACK}
ENH_ZH={'Bonus':'额外','Mult':'倍率','Wild':'万能','Glass':'玻璃','Steel':'钢铁','Gold':'黄金','Lucky':'幸运','Stone':'石头'}
ED_ZH={'Foil':'镀箔','Holographic':'镭射','Polychrome':'多彩','Negative':'负片'}
SEAL_ZH={'Red':'红印','Gold':'金印','Blue':'蓝印','Purple':'紫印'}
def wid(s):
 s=ESC.sub('',str(s));x=0
 for c in s:
  if unicodedata.combining(c):continue
  x+=2 if unicodedata.east_asian_width(c) in ('W','F') or ord(c)>0xffff else 1
 return x
def trim(s,n):
 if wid(s)<=n:return s
 ans=''
 for c in ESC.sub('',s):
  if wid(ans+c+'…')>n:break
  ans+=c
 return ans+'…'
def pad(s,n,align='left'):
 s=trim(str(s),n);gap=max(0,n-wid(s))
 if align=='center':return ' '*(gap//2)+s+' '*(gap-gap//2)
 if align=='right':return ' '*gap+s
 return s+' '*gap

def card_art(c,idx):
 rank=(c.rank if c.enhancement!='Stone' else '★');suit=c.suit
 def line(content):return CARD_BG+CARD_EDGE+'│'+content+CARD_EDGE+'│'+RESET
 top=CARD_BG+CARD_EDGE+'╭'+'─'*9+'╮'+RESET
 bot=CARD_BG+CARD_EDGE+'╰'+'─'*9+'╯'+RESET
 marker=(ENH_ZH.get(c.enhancement,'') or ED_ZH.get(c.edition,'') or SEAL_ZH.get(c.seal,''))[:3]
 mark=pad(marker,8,'center')
 return [top,
         line(' '+RANK_COLOR[suit]+pad(rank,2)+CARD_EDGE+' '*6),
         line(' '*4+SUIT_COLOR[suit]+suit+CARD_EDGE+' '*4),
         line(' '+BLACK+mark+CARD_EDGE),
         line(' '+BLACK+pad(str(idx),2)+CARD_EDGE+' '*6),bot]

def cards_block(cards):
 if not cards:return [MUTED+'（暂无手牌）'+RESET]
 result=[]
 # 8 cards/row needs ~96 columns; adapt to 4 cards on narrow terminal
 cols=8 if shutil.get_terminal_size((124,45)).columns>=110 else 6 if shutil.get_terminal_size((110,45)).columns>=88 else 4
 for start in range(0,len(cards),cols):
  group=[card_art(c,i+1) for i,c in enumerate(cards[start:start+cols],start)]
  for r in range(6):result.append(' '.join(a[r] for a in group))
 return result

def full_name(typ,name):
 if typ=='Joker':return LOOKUP[name].zh if name in LOOKUP else name
 if typ=='Tarot':return TAROT_ZH.get(name,name)
 if typ=='Planet':return PLANET_ZH.get(name,name)
 if typ=='Spectral':return SPECTRAL_ZH.get(name,name)
 return name

def fmt_points(n):
 try:
  if int(n)<1_000_000_000_000:return f'{int(n):,}'
  exp=len(str(int(n)))-1
  return f'{str(int(n))[:3][0]}.{str(int(n))[:3][1:]}e{exp}'
 except Exception:return str(n)

def content(g):
 lines=[]
 mode={'blind':'准备阶段','play':'牌局进行中','shop':'商店','pack':'打开补充包','lost':'游戏结束'}.get(g.state,g.state)
 lines.append('')
 lines.append(GOLD+'◆   B A L A T R O   ◆'+RESET)
 lines.append(MUTED+'纯文字扑克 Roguelike  ·  中文街机版  ·  macOS Terminal'+RESET)
 lines.append('')
 lines.append('   '+AQUA+f'ANTE {g.ante}'+RESET+'     '+WHITE+g.blind_name()+RESET+'     '+(GREEN if g.state=='shop' else GOLD)+mode+RESET+'     '+GOLD+f'${g.money}'+RESET)
 width=64
 ratio=min(1,g.score/max(1,g.target))
 filled=int(width*ratio)
 lines.append('   '+GREEN+'█'*filled+MUTED+'░'*(width-filled)+RESET)
 lines.append('   '+WHITE+'当前得分  '+AQUA+fmt_points(g.score)+RESET+'   /   '+WHITE+'目标  '+ORANGE+fmt_points(g.target)+RESET)
 lines.append('   '+MUTED+f'出牌 {g.hands}/{g.max_hands}     弃牌 {g.discards}/{g.max_discards}     小丑 {len(g.jokers)}/{g.joker_slots}     牌组 {len(g.deck)} 张'+RESET)
 if g.won:lines.append(GREEN+'   ★ 已通关第 8 底注 · 无尽模式进行中 ★'+RESET)
 if g.boss and g.blind==2:
  dis='（已失效）' if g.boss_disabled or g.has('Chicot') else ''
  lines.append(RED+f'   BOSS：{BOSS_ZH.get(g.boss,g.boss)} · {BOSSES[g.boss]} {dis}'+RESET)
 lines.append('')
 lines.append(GOLD+'━━  小 丑 区   J O K E R S  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'+RESET)
 if not g.jokers:lines.append('    '+MUTED+'当前没有小丑牌。通关后可在商店中购买。'+RESET)
 else:
  for k,j in enumerate(g.jokers,1):
   info=LOOKUP[j['name']];ed=ED_ZH.get(j.get('edition',''),'');rar={'Common':'普通','Uncommon':'罕见','Rare':'稀有','Legendary':'传说'}[info.rarity]
   color={'Common':WHITE,'Uncommon':GREEN,'Rare':MAGENTA,'Legendary':GOLD}[info.rarity]
   lines.append(f'    {GOLD}{k:>2}{RESET}  {color}{pad(info.zh,16)}{RESET} {MUTED}〔{rar}{"/"+ed if ed else ""}〕{RESET}  '+trim(info.desc,55))
 lines.append('')
 if g.state=='pack' and g.pack:
  p=g.pack
  lines.append(GOLD+f'━━  {PACK_KINDS[p["kind"]]}   剩余选择 {p["picks"]} 次  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'+RESET)
  for i,o in enumerate(p['options'],1):
   label=full_name(o['type'],o['name']);ed=ED_ZH.get(o.get('edition',''),'')
   lines.append('    '+AQUA+f'[{i}] '+RESET+WHITE+pad(label,18)+RESET+MUTED+(' '+ed if ed else '')+RESET)
 elif g.state=='shop':
  lines.append(GOLD+'━━  商 店   S H O P  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'+RESET)
  for i,item in enumerate(g.shop,1):
   label=full_name(item['type'],item['name']);ed=ED_ZH.get(item.get('edition',''),'')
   lines.append('    '+AQUA+f'[买 {i}]  '+RESET+pad(label,20)+MUTED+'  '+pad(ed,8)+RESET+GOLD+f'  ${item["cost"]}'+RESET)
  if not g.shop:lines.append('    '+MUTED+'商品已售罄。'+RESET)
  lines.append('')
  for i,p in enumerate(g.packs,1):
   size={'Normal':'普通','Jumbo':'大型','Mega':'巨型'}[p['size']]
   lines.append('    '+GREEN+f'[开包 {i}]  '+RESET+pad(f'{size}{PACK_KINDS[p["kind"]]}',20)+GOLD+f'  ${p["cost"]}'+RESET)
  if g.shop_voucher:
   vo=VOUCHERS[g.shop_voucher]
   lines.append('    '+MAGENTA+f'[优惠]  {g.shop_voucher}'+RESET+MUTED+' · '+vo['desc']+RESET+GOLD+f'  ${g.apply_cost(10)}'+RESET)
  else:lines.append('    '+MUTED+'本商店优惠券已购买。'+RESET)
 else:
  lines.append(GOLD+'━━  扑 克   Y O U R  H A N D  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'+RESET)
 if g.hand:
  if g.state=='shop':lines.append(AQUA+'━━  目标手牌  ·  可用于塔罗与幻灵牌  ━━━━━━━━━━━━━━━━━━━━━━━━━━'+RESET)
  lines.extend('  '+x for x in cards_block(g.hand))
 elif g.state not in ('shop',):lines.append('   '+MUTED+'暂无手牌。'+RESET)
 lines.append('')
 if g.consumables:
  cs='    '.join(f'[{i}]'+full_name(c['type'],c['name']) for i,c in enumerate(g.consumables,1))
 else:cs='（空）'
 lines.append(GOLD+'━━  消 耗 牌  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'+RESET)
 lines.append('   '+WHITE+cs+RESET)
 if g.last_result:
  r=g.last_result
  lines.append('')
  lines.append('   '+AQUA+f'最近出牌  {HAND_ZH.get(r["hand"],r["hand"])}'+RESET+'   '+BLUE+fmt_points(r['chips'])+' 筹码'+RESET+' × '+RED+fmt_points(r['mult'])+' 倍率'+RESET+' = '+GOLD+fmt_points(r['points'])+RESET)
 lines.append('')
 lines.append(GOLD+'━━  操 作  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'+RESET)
 ops={'blind':'开始 · 跳关 · 换Boss · 存档 · 退出','play':'出 1 2 3 4 5 · 弃 1 2 · 使用 1 2 · 存档','shop':'买 1 · 开包 1 · 优惠 · 刷新 · 卖 1 · 下一关','pack':'选择 1 [目标牌号] · 跳过','lost':'新游戏 · 读档 · 退出'}.get(g.state,'帮助')
 lines.append('   '+GREEN+ops+RESET)
 lines.append('   '+MUTED+'输入 帮助 查看完整操作；输入 图鉴 查看150张小丑；输入 牌型 查看等级'+RESET)
 for msg in g.log[-2:]:lines.append('   '+MUTED+'· '+trim(msg,78)+RESET)
 return lines

def display(g,force=False):
 term=shutil.get_terminal_size((124,48));w=term.columns;h=term.lines
 lines=content(g)
 if w<82:
  if sys.stdout.isatty():sys.stdout.write('\033[2J\033[H')
  print('终端宽度不足，请把 Terminal 窗口调整到至少 100 列（推荐 122×46）。');return
 frame_width=min(116,w-2)
 height=len(lines)+2
 left=max(0,(w-frame_width)//2)
 up=max(0,(h-height)//2) if h>height else 0
 border=GOLD+'╔'+'═'*(frame_width-2)+'╗'+RESET
 bottom=GOLD+'╚'+'═'*(frame_width-2)+'╝'+RESET
 output=[]
 output.extend(['']*up)
 output.append(' '*left+border)
 for s in lines:
  plain=wid(s)
  if plain>frame_width-4:s=trim(s,frame_width-4);plain=wid(s)
  output.append(' '*left+GOLD+'║'+RESET+' '+s+' '*max(0,frame_width-4-plain)+' '+GOLD+'║'+RESET)
 output.append(' '*left+bottom)
 if sys.stdout.isatty():sys.stdout.write('\033[2J\033[H')
 print('\n'.join(output))
 if h<height+2:print(MUTED+'提示：增大终端窗口高度可让画面完整显示。'+RESET)

def show_help():
 print('''
╔═══════════════════  中文游戏帮助  ═══════════════════╗
║  开始                 开始当前盲注                    ║
║  出 1 2 3 4 5         打出指定手牌（最多五张）       ║
║  弃 1 2               丢弃指定手牌（最多五张）       ║
║  使用 1 2 3          使用消耗牌1，对手牌2、3生效    ║
║  买 1                 购买商店商品1                  ║
║  开包 1               打开第一个补充包                ║
║  选择 1 2             选择第一张补充包牌，对手牌2使用║
║  跳过                 在补充包中跳过剩余选择          ║
║  优惠                 购买商店优惠券                  ║
║  卖 1                 出售第一张小丑牌                ║
║  换位 1 2             交换两个小丑的结算位置          ║
║  刷新                 重新生成商店的商品牌            ║
║  下一关               离开商店进入下一盲注          ║
║  跳关                 跳过未开始的小/大盲注          ║
║  换Boss               使用导演剪辑优惠券重掷Boss    ║
║  牌型 / 图鉴 [页码]   查看牌型等级 / 150张小丑资料  ║
║  存档 / 读档 / 新游戏 / 退出                         ║
╚══════════════════════════════════════════════════════╝
花色：♥ 红   ♦ 橙   ♠ 黑   ♣ 绿
字面点数：红花色用红字，黑花色用黑字；所有牌均有浅色底。
''')
 input('按回车返回游戏...')

def show_collection(page=1):
 pages=(len(JOKERS)+11)//12
 page=max(1,min(pages,page))
 print(f'\n{GOLD}【150 张 Joker 图鉴】第 {page}/{pages} 页{RESET}\n')
 for i,j in enumerate(JOKERS[(page-1)*12:page*12],(page-1)*12+1):
  rarity={'Common':'普','Uncommon':'罕','Rare':'稀','Legendary':'传'}[j.rarity]
  print(f'{i:>3}. {pad(j.zh,14)} [{rarity}] {j.desc}'+('  [部分实现]' if j.status=='partial' else ''))
 print('\n提示：图鉴 2 可看第二页。')
 input('按回车返回游戏...')

def show_levels(g):
 print('\n'+GOLD+'【牌型与等级】'+RESET)
 for name,level in g.levels.items():
  base=HANDS[name];print(f'  {pad(HAND_ZH[name],12)} Lv.{level:<3} · {base[0]+(level-1)*base[2]} 筹码 × {base[1]+(level-1)*base[3]} 倍率 · {PLANET_ZH[name]}')
 input('\n按回车返回游戏...')
