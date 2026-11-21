"""Transparent score formulas; sourced from the same run as the scoring engine."""
from __future__ import annotations
from .poker import HAND_ZH
from fractions import Fraction

def number(n):
    n=float(n)
    if abs(n)<1e-10:n=0.0
    if abs(n-round(n))<1e-9:return f'{round(n):,}'
    fraction=Fraction(n).limit_denominator(128)
    if fraction.denominator>1 and abs(float(fraction)-n)<1e-10*max(1,abs(n)):
        d=fraction.denominator
        while d%2==0:d//=2
        while d%5==0:d//=5
        if d>1:return f'{fraction.numerator}/{fraction.denominator}'
    return f'{n:,.8f}'.rstrip('0').rstrip('.')

def part(base,bonus):
    # Omit any zero component; show a negative gain with a minus, not "+ -".
    if abs(bonus)<1e-10:return number(base)
    if abs(base)<1e-10:return number(bonus)
    sign=' + ' if bonus>0 else ' − '
    return '('+number(base)+sign+number(abs(bonus))+')'

def score_formula(result):
    hand=HAND_ZH.get(result['hand'],result['hand'])
    b=result.get('breakdown')
    if not b:
        return f"{hand}：{number(result['chips'])} × {number(result['mult'])} = {result['points']:,}"
    chips=part(b['base_chips'],b['bonus_chips'])
    mult=part(b['base_mult'],b['bonus_mult'])
    f=b.get('xmult',1)
    multiplier=(' × '+number(f)) if abs(f-1)>1e-10 else ''
    return f"{hand}：{chips} × {mult}{multiplier} = {result['points']:,}"
