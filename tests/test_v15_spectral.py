"""Focused V15 regression checks for all Spectral effects and boss interactions."""
import unittest
from unittest.mock import patch
from arcana.game import Game
from arcana.cards import Card
from arcana.content import SPECTRALS
from play import Controller


class SpectralAudit(unittest.TestCase):
    def game(self, seed=40):
        g=Game.new_run(seed=seed)
        g.start_blind()
        return g

    def put_and_use(self,g,name,targets=None):
        g.consumables=[{'type':'Spectral','name':name}]
        g.use(0,targets)
        self.assertEqual(g.consumables,[],name)

    def test_catalog_18_effects(self):
        self.assertEqual(len(SPECTRALS),18)
        for name in SPECTRALS:
            with self.subTest(name=name):
                g=self.game(seed=45)
                if name in ('Ankh','Hex','Ectoplasm'):
                    g.add_joker('Joker');g.add_joker('Greedy Joker')
                if name=='Wraith':g.money=17
                target=[0] if name in ('Talisman','Aura','Deja Vu','Trance','Medium','Cryptid') else None
                prev=g.hand_size
                self.put_and_use(g,name,target)
                if name=='Sigil':self.assertEqual(len({c.suit for c in g.hand}),1)
                if name=='Ouija':
                    self.assertEqual(len({c.rank for c in g.hand}),1)
                    self.assertEqual(g.hand_size,prev-1)
                if name=='Wraith':self.assertEqual(g.money,0)
                if name=='The Soul':self.assertEqual(len(g.jokers),1)
                if name=='Black Hole':self.assertEqual(len(set(g.levels.values())),1)
                if name=='Aura':self.assertTrue(any(c.edition for c in g.hand))
                if name in ('Talisman','Deja Vu','Trance','Medium'):
                    self.assertTrue(any(c.seal for c in g.hand))

    def test_familiar_grim_incantation_add_to_hand_and_deck(self):
        for name,n,ranks in [('Familiar',3,{'J','Q','K'}),('Grim',2,{'A'}),('Incantation',4,set('23456789')|{'10'})]:
            with self.subTest(name=name):
                g=self.game();before={c.uid for c in g.hand};old_deck=len(g.deck);old_hand=len(g.hand)
                self.put_and_use(g,name)
                created=[c for c in g.hand if c.uid not in before]
                self.assertEqual(len(created),n)
                self.assertEqual(len(g.hand),old_hand-1+n)
                self.assertEqual(len(g.deck),old_deck-1+n)
                self.assertTrue(all(c.rank in ranks and c.enhancement for c in created))
                for c in created:
                    self.assertTrue(any(d.uid==c.uid for d in g.deck))

    def test_cryptid_creates_two_hand_cards_and_preserves_traits(self):
        g=self.game()
        g.hand[0].enhancement='Glass';g.hand[0].seal='Red'
        exemplar=g.hand[0];old_hand=len(g.hand);old_deck=len(g.deck)
        self.put_and_use(g,'Cryptid',[0])
        self.assertEqual(len(g.hand),old_hand+2)
        self.assertEqual(len(g.deck),old_deck+2)
        clones=[c for c in g.hand if c.uid!=exemplar.uid and c.rank==exemplar.rank and c.suit==exemplar.suit and c.enhancement=='Glass' and c.seal=='Red']
        self.assertGreaterEqual(len(clones),2)

    def test_hex_and_ankh_protect_eternal_jokers(self):
        for name in ('Hex','Ankh'):
            with self.subTest(name=name):
                g=self.game();g.add_joker('Joker');g.add_joker('Greedy Joker');g.add_joker('Lusty Joker')
                g.jokers[0]['eternal']=True
                g.rng.seed(24)
                self.put_and_use(g,name)
                self.assertTrue(any(j.get('eternal') and j['name']=='Joker' for j in g.jokers))
                if name=='Ankh':self.assertGreaterEqual(len(g.jokers),2)
                else:self.assertTrue(any(j.get('edition')=='Polychrome' for j in g.jokers))

    def test_ectoplasm_escalates_hand_size_loss(self):
        g=self.game();g.add_joker('Joker');g.add_joker('Greedy Joker')
        before=g.hand_size
        self.put_and_use(g,'Ectoplasm')
        self.assertEqual(g.hand_size,before-1)
        self.put_and_use(g,'Ectoplasm')
        self.assertEqual(g.hand_size,before-3)
        self.assertEqual(g.joker_state['Ectoplasm_used'],2)

    def test_failed_spectral_does_not_consume(self):
        g=self.game();g.consumables=[{'type':'Spectral','name':'Wraith'}]
        for _ in range(g.joker_slots):g.add_joker('Joker')
        with self.assertRaises(ValueError):g.use(0)
        self.assertEqual(g.consumables[0]['name'],'Wraith')
        g=self.game();g.hand=g.hand[:1];g.consumables=[{'type':'Spectral','name':'Sigil'}]
        with self.assertRaises(ValueError):g.use(0)
        self.assertEqual(g.consumables[0]['name'],'Sigil')

    def test_verdant_leaf_joker_sale_via_inventory(self):
        c=Controller();g=Game.new_run(seed=44);g.add_joker('Joker')
        g.blind=2;g.boss='Verdant Leaf';g.start_blind()
        c.game=g;c.ui.overlay='hand';c.ui.inventory_page=0;c.ui.inventory_cursor=0
        self.assertTrue(g.debuff(g.hand[0]))
        c.key('BACKSPACE')
        self.assertEqual(len(g.jokers),0)
        self.assertTrue(g.boss_disabled)
        self.assertFalse(g.debuff(g.hand[0]))
        self.assertEqual(c.ui.overlay,'hand')

    def test_verdant_eternal_cannot_sell(self):
        c=Controller();g=Game.new_run(seed=44);g.add_joker('Joker');g.jokers[0]['eternal']=True
        g.blind=2;g.boss='Verdant Leaf';g.start_blind()
        c.game=g;c.ui.overlay='hand';c.ui.inventory_cursor=0
        c.key('BACKSPACE')
        self.assertFalse(g.boss_disabled)
        self.assertEqual(len(g.jokers),1)

    def test_cerulean_forced_selection_and_cannot_toggle(self):
        c=Controller();g=Game.new_run(seed=44);g.blind=2;g.boss='Cerulean Bell'
        c.game=g;c.confirm()
        self.assertEqual(c.ui.selected_uids,[g.locked_card])
        c.ui.cursor_hand=next(i for i,card in enumerate(g.hand) if card.uid==g.locked_card)
        c.confirm();self.assertEqual(c.ui.selected_uids,[g.locked_card])
        c.execute('p')
        if g.state=='play':self.assertEqual(c.ui.selected_uids,[g.locked_card])

    def test_english_psychic_blocked_preview_and_score_are_english(self):
        import os,re
        from unittest.mock import patch
        from arcana.tui import UI
        u=UI(language='en')
        g=Game.new_run(seed=16);g.blind=2;g.boss='The Psychic';g.start_blind()
        u.selected_uids=[g.hand[0].uid]
        captures=[]
        with patch('arcana.tui.shutil.get_terminal_size',return_value=os.terminal_size((165,65))):
            u.renderer.draw=lambda cv:captures.append(''.join(cell.text for row in cv.a for cell in row))
            u.draw(g)
            self.assertNotRegex(captures[-1],r'[\u3400-\u9fff]')
            g.play([0])
            u.draw(g)
            self.assertNotRegex(captures[-1],r'[\u3400-\u9fff]')

    def test_serpent_draws_three_even_above_capacity(self):
        g=self.game();g.blind=2;g.boss='The Serpent';g.boss_disabled=False
        before=len(g.hand);self.assertEqual(before,8)
        g.discard([0])
        self.assertEqual(len(g.hand),before-1+3)
        self.assertGreater(len(g.hand),g.effective_hand_size())

    def test_english_dynamic_notices_have_no_chinese(self):
        import re
        c=Controller(language='en')
        for msg in ('符印：全部 8 张手牌变成 ♥','通灵板：全部 8 张手牌变成 A，手牌容量 -1',
                    '已使用效果牌：Sigil','未执行：无法使用效果牌','翠绿叶片：出售小丑后 Boss 失效'):
            c.note(msg)
            self.assertFalse(re.search(r'[\u3400-\u9fff]',c.ui.message),c.ui.message)

    def test_joker_restriction_uses_identity_with_duplicate_names(self):
        g=self.game()
        g.add_joker('Joker');g.add_joker('Joker')
        g.blind=2;g.boss='Crimson Heart';g.boss_disabled=False
        for j in g.jokers:j.pop('debuff_round',None)
        g.jokers[0]['debuff_round']=True
        # Scoring a hand must disable the other physical Joker on the next play.
        g.play([0])
        self.assertTrue(g.jokers[1].get('debuff_round'))

if __name__=='__main__':unittest.main()
