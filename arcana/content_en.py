"""English fallback for gameplay descriptions when a locale-specific rule is unavailable.

Hand-authored descriptions follow this game's implemented rules, not external
third-party localization files. Names/major menus use the selected UI locale.
"""
from .content import NAMES

_JOKER_ROWS='''
+4 Mult|+3 Mult per scoring Diamond|+3 Mult per scoring Heart|+3 Mult per scoring Spade|+3 Mult per scoring Club|+8 Mult when played hand contains a Pair|+12 Mult with Three of a Kind|+10 Mult with Two Pair|+12 Mult with Straight|+10 Mult with Flush
+50 Chips with Pair|+100 Chips with Three of a Kind|+80 Chips with Two Pair|+100 Chips with Straight|+80 Chips with Flush|+20 Mult with up to 3 cards played|XMult based on empty Joker slots|Straights and Flushes can use 4 cards|Retrigger held-card effects|May go into debt down to -$20
At Blind start, consume Joker to the right for permanent Mult|+30 Chips per discard remaining|+15 Mult with no discards remaining|Add a Stone card each Blind|Every sixth hand gains ×4 Mult|Scoring 8 may create Tarot card|Random +0–23 Mult|Retrigger cards on last hand|Mult based on lowest held rank|One free shop reroll
Scoring A,2,3,5,8 adds +8 Mult|XMult grows with Steel cards in deck|Face cards give +30 Chips|+3 Mult per Joker|Money if no discards used|Retrigger scoring ranks 2–5|All cards count as face cards|+15 Mult; may expire|Even-rank scoring cards give +4 Mult|Odd-rank scoring cards give +31 Chips
Scoring A: +20 Chips and +4 Mult|Scoring face cards can pay $2|Mult equals number of plays of hand type|Build Mult until scoring a face card|Chance to level up played hand|Sell value grows after each round|+3 hands, no discards|×3 Mult if all held cards are black suits|Playing Straight permanently increases Chips|Large Chips bonus, decays each hand
First single-card hand duplicates that card|All played cards score|+2 Chips per card in draw pile|First single 6 creates Spectral|Using Planet cards grows XMult|Scored cards permanently gain Chips|Discard three face cards for $5|Playing raises Mult; discarding lowers it|A Straight containing Ace can create Tarot|Specific hand type earns $4
×3 Mult, small chance to disappear|×3 Mult on repeated hand types|Permanent Mult for skipped packs|Grows XMult, may destroy other Joker|Gain Chips for each four-card play|Straight Flush can generate Spectral|Create two Common Jokers at Blind start|Consume enhancements for XMult|Straights may skip ranks|Add cards to deck to grow XMult
Tarot when low on money|Each held King contributes ×1.5 Mult|Income based on number of 9s in deck|Money at round end; grows with Boss wins|XMult grows by avoiding most played hand|Scored face cards become Gold|Sell to disable Boss|First scoring face card ×2 Mult|Increase sell values each round|Hand capacity bonus, decays
+4 Mult for each missing card below 52|Held face cards can pay $1|Discard target rank for $5|Additional interest income|Chance to create Tarot when opening packs|+Mult for Tarot cards used|Hand capacity +1|One extra discard|More Stone cards in deck yield Chips|Earn $4 at round end
Lucky card triggers increase XMult|Each Uncommon Joker provides ×1.5 Mult|+2 Chips per $1 owned|Sell for Double Tags|First single-card discard destroys it and earns $3|Each shop reroll adds +2 Mult|Starts at +20 Mult, decreases each round|Two Pair grows permanent Mult|Scoring target suit grants ×1.5 Mult|Starts at ×2 Mult, weakens when discarding
Scoring 10 and 4 adds Chips and Mult|Retrigger scored cards for a limited time|Discard target suit for more Chips|Face cards give +5 Mult|Selling cards accumulates XMult|Scoring Gold cards pay $4|Survive one failed Blind at 25% score|×3 Mult on the last hand|Retrigger face cards|Gain Mult based on other Jokers' sell values
+2 hand capacity, -1 hand play|Add a sealed card each Blind|Hearts/Diamonds combine; Spades/Clubs combine|Skipping Blinds grows XMult|First scored card triggers twice more|Scoring Diamonds earns $1|Scoring Hearts may ×1.5 Mult|Scoring Spades gives +50 Chips|Scoring Clubs gives +7 Mult|Broken Glass cards grow XMult
Shop duplicates may appear|Four different scoring suits give ×3 Mult|Copy the Joker to the right|Scoring 2 gives permanent Chips|More discards, smaller hand|Double most odds|Specified scoring rank and suit gives ×2 Mult|Club plus another scoring suit gives ×2 Mult|Money when Boss debuff triggers|Discard Jacks for growing XMult
Pair gives ×2 Mult|Three of a Kind gives ×3 Mult|Four of a Kind gives ×4 Mult|Straight gives ×3 Mult|Flush gives ×2 Mult|+250 Chips and -2 hand capacity|Sell after two rounds to copy a Joker|Copy leftmost Joker|Earn income from different Planet types|Each held Queen adds +13 Mult
×3 Mult with at least 16 enhanced cards|Tarot card when entering Blind|Planet cards and Celestial packs are free|First discard upgrades its hand type|+2 Mult per $5 owned|Destroying face cards grows XMult|Scoring Kings and Queens ×2 Mult|Discarded cards build XMult|Disable Boss abilities|Copy a Negative consumable when leaving shop
'''
_desc=[v.strip() for row in _JOKER_ROWS.strip().splitlines() for v in row.split('|')]
assert len(_desc)==len(NAMES),(len(_desc),len(NAMES))
JOKER_EN=dict(zip(NAMES,_desc))

TAROT_EN={
'The Fool':'Create the last used Tarot or Planet card (not another Fool).',
'The Magician':'Convert up to 2 selected cards into Lucky Cards.',
'The High Priestess':'Create up to 2 random Planet cards, subject to available slots.',
'The Empress':'Convert up to 2 selected cards into Mult Cards.',
'The Emperor':'Create up to 2 random Tarot cards, subject to available slots.',
'The Hierophant':'Convert up to 2 selected cards into Bonus Cards.',
'The Lovers':'Convert one selected card into a Wild Card.',
'The Chariot':'Convert one selected card into a Steel Card.',
'Justice':'Convert one selected card into a Glass Card.',
'The Hermit':'Double current money, gaining at most $20.',
'The Wheel of Fortune':'1 in 4 chance to give a random Joker a special edition.',
'Strength':'Increase the rank of up to 2 selected cards by one.',
'The Hanged Man':'Permanently destroy up to 2 selected cards.',
'Death':'Transform the first selected card into a copy of the second.',
'Temperance':'Gain money equal to total Joker sell value, up to $50.',
'The Devil':'Convert one selected card into a Gold Card.',
'The Tower':'Convert one selected card into a Stone Card.',
'The Star':'Convert up to 3 selected cards into Diamonds.',
'The Moon':'Convert up to 3 selected cards into Clubs.',
'The Sun':'Convert up to 3 selected cards into Hearts.',
'Judgement':'Create one random Joker if a slot is available.',
'The World':'Convert up to 3 selected cards into Spades.',
}
SPECTRAL_EN={
'Familiar':'Destroy one random card in hand; add 3 enhanced face cards to the deck.',
'Grim':'Destroy one random card in hand; add 2 enhanced Aces.',
'Incantation':'Destroy one random card in hand; add 4 enhanced number cards.',
'Talisman':'Apply a Gold Seal to one selected card.',
'Aura':'Give one selected card a random edition.',
'Wraith':'Create one Rare Joker and set money to $0.',
'Sigil':'Convert all current hand cards into a single random suit.',
'Ouija':'Convert all current hand cards into a single random rank; hand capacity -1.',
'Ectoplasm':'Apply Negative edition to a random Joker; hand capacity -1.',
'Immolate':'Destroy up to 5 random hand cards and gain $20.',
'Ankh':'Duplicate a random Joker and remove other Jokers.',
'Deja Vu':'Apply a Red Seal to one selected card.',
'Hex':'Give one Joker Polychrome and remove other Jokers.',
'Trance':'Apply a Blue Seal to one selected card.',
'Medium':'Apply a Purple Seal to one selected card.',
'Cryptid':'Duplicate one selected hand card twice into the deck.',
'The Soul':'Create one Legendary Joker if a slot is available.',
'Black Hole':'Increase the level of every poker hand by one.',
}
ENHANCEMENT_EN={'Bonus':'Scoring this card adds +30 Chips','Mult':'Scoring this card adds +4 Mult','Wild':'Counts as any suit for Flushes, unless debuffed','Glass':'×2 Mult when scoring; 1 in 4 break chance','Steel':'×1.5 Mult while held in hand','Gold':'Earn $3 at end of the round while held','Lucky':'1 in 5: +20 Mult; 1 in 15: earn $20','Stone':'+50 Chips; has no suit or rank for hand formation'}
EDITION_EN={'Foil':'+50 Chips when scoring','Holographic':'+10 Mult when scoring','Polychrome':'×1.5 Mult when scoring','Negative':'Does not occupy a normal Joker slot'}
SEAL_EN={'Red':'Retrigger this card once','Gold':'Earn money when scored','Blue':'Create Planet card at round end','Purple':'Create Tarot card when discarded'}

def description(typ,name):
    if typ=='Joker':return JOKER_EN.get(name,'Special Joker ability')
    if typ=='Tarot':return TAROT_EN.get(name,'Tarot effect')
    if typ=='Spectral':return SPECTRAL_EN.get(name,'Spectral effect')
    if typ=='Planet':return 'Permanently increase the level of '+name
    if typ=='Enhancement':return ENHANCEMENT_EN.get(name,'Card enhancement')
    if typ=='Edition':return EDITION_EN.get(name,'Card edition')
    if typ=='Seal':return SEAL_EN.get(name,'Card seal')
    return 'See the item details for its effect'
