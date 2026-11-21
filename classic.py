#!/usr/bin/env python3
"""Balatro — standalone, standard-library-only macOS terminal game."""
import sys
from arcana.game import Game,SAVE
from arcana.ui import display,show_help,show_levels,show_collection

def numbers(parts):
 out=[]
 for p in parts:
  for v in p.replace(',',' ').replace('，',' ').split():out.append(int(v)-1)
 return out

def main():
 g=Game()
 while True:
  display(g)
  try:
   line=input('\n  ◇ 输入指令 ›  ').strip()
  except (EOFError,KeyboardInterrupt):
   print('\n已退出，感谢游玩。');break
  if not line:continue
  cmd=line.split();op=cmd[0].lower();args=cmd[1:]
  try:
   if op in ('退出','quit','q','exit'):
    g.save();print('游戏已自动保存。');break
   elif op in ('帮助','help','h','?'):show_help()
   elif op in ('新游戏','new','restart'):g=Game();g.note('新的冒险开始！')
   elif op in ('存档','save'):g.save();g.note('已保存到 '+str(SAVE))
   elif op in ('读档','load'):g=Game.load();g.note('已读取存档')
   elif op in ('开始','start'):g.start_blind()
   elif op in ('跳关','skipblind'):g.skip_blind()
   elif op in ('换boss','换Boss','boss'):g.reroll_boss()
   elif op in ('出','打','p','play'):g.play(numbers(args))
   elif op in ('弃','d','discard'):g.discard(numbers(args))
   elif op in ('使用','u','use'):g.use(int(args[0])-1,numbers(args[1:]))
   elif op in ('买','购买','b','buy'):g.buy(int(args[0])-1)
   elif op in ('开包','open'):g.open_pack(int(args[0])-1)
   elif op in ('选择','take'):g.select_pack(int(args[0])-1,numbers(args[1:]))
   elif op in ('跳过','pass') and g.state=='pack':g.skip_pack()
   elif op in ('跳过','pass') and g.state=='blind':g.skip_blind()
   elif op in ('优惠','voucher','v'):g.buy_voucher()
   elif op in ('刷新','reroll'):g.reroll()
   elif op in ('卖','sell'):g.sell_joker(int(args[0])-1)
   elif op in ('换位','swap'):
    a,b=numbers(args[:2]);g.jokers[a],g.jokers[b]=g.jokers[b],g.jokers[a];g.note('小丑位置已交换')
   elif op in ('下一关','next'):g.next_blind()
   elif op in ('牌型','levels'):show_levels(g)
   elif op in ('图鉴','collection'):show_collection(int(args[0]) if args else 1)
   else:g.note('未知命令；输入「帮助」查看说明')
  except (ValueError,IndexError,KeyError,TypeError,AttributeError) as e:g.note('操作失败：'+str(e))

if __name__=='__main__':
 try:main()
 except Exception as e:
  print('\n发生意外错误：',e)
  print('可重新运行并使用「读档」恢复。')
  raise
