"""Lightweight, offline interface localization for the macOS terminal edition.

Translations are original UI strings, not third-party game localization files.
Chinese remains the reference language for complex, hand-authored card rules.
"""
from __future__ import annotations
import json
from pathlib import Path

# ISO-like codes deliberately stable across releases and across saves.
LANGUAGES = (
    ('zh_CN','简体中文'), ('zh_TW','繁體中文'), ('en','English'),
    ('ja','日本語'), ('ko','한국어'), ('fr','Français'), ('es','Español'),
    ('de','Deutsch'), ('it','Italiano'), ('pt_BR','Português (Brasil)'),
    ('ru','Русский'), ('nl','Nederlands'), ('tr','Türkçe'), ('pl','Polski'),
    ('ar','العربية'), ('hi','हिन्दी'), ('id','Bahasa Indonesia'), ('vi','Tiếng Việt'),
)
LANGUAGE_NAMES = dict(LANGUAGES)
CONFIG_PATH = Path.home()/'.balatro_terminal_settings.json'

# These are the interactive interface terms. If a translation is unavailable,
# fall back to English, never to an invented machine translation of an effect.
KEYS = (
    'language','choose_language','language_hint','language_saved','selected_language',
    'confirm','cancel','back','continue','start','help','deck','stake','shop','blind',
    'boss','jokers','consumables','cards','my_cards','full_deck','packs',
    'vouchers','score','target_score','money','hand','hands','discards',
    'levels','poker_hands','buy','sell','use','details','next_round','save','load',
    'quit','music','settings','completed','challenge','current','select','no_cards',
    'arcana_pack','celestial_pack','spectral_pack','standard_pack','buffoon_pack',
)
# Entries correspond to KEYS, separated by a literal pipe; short terms are
# favoured so narrow terminal panes remain readable.
DATA = {
'en': 'Language|Choose language|W/S or ↑↓: move  ·  Enter: apply  ·  Esc: cancel|Language saved|Current language|Confirm|Cancel|Back|Continue|Start|Help|Deck|Stake|Shop|Blind|Boss|Jokers|Consumables|Cards|My Cards|Full Deck|Packs|Vouchers|Score|Target|Money|Hand|Hands|Discards|Levels|Poker Hands|Buy|Sell|Use|Details|Next Round|Save|Load|Quit|Music|Settings|Completed|Challenge|Current|Select|No cards|Arcana Pack|Celestial Pack|Spectral Pack|Standard Pack|Buffoon Pack',
'zh_CN': '语言|选择语言|W/S 或 ↑↓ 选择 · Enter 确认 · Esc 取消|语言已保存|当前语言|确认|取消|返回|继续|开始|帮助|牌组|难度|商店|盲注|Boss|小丑牌|效果牌|卡牌|持有卡牌|整套牌组|补充包|优惠券|分数|目标分数|金币|手牌|出牌次数|弃牌次数|等级|牌型|购买|出售|使用|详情|下一轮|保存|读取|退出|音乐|设置|已完成|挑战|当前|选择|无卡牌|奥秘包|天体包|幻灵包|标准包|小丑包',
'zh_TW': '語言|選擇語言|W/S 或 ↑↓ 選擇 · Enter 確認 · Esc 取消|語言已儲存|目前語言|確認|取消|返回|繼續|開始|說明|牌組|難度|商店|盲注|Boss|小丑牌|效果牌|卡牌|持有卡牌|整套牌組|補充包|優惠券|分數|目標分數|金幣|手牌|出牌次數|棄牌次數|等級|牌型|購買|出售|使用|詳情|下一輪|儲存|讀取|退出|音樂|設定|已完成|挑戰|目前|選擇|無卡牌|奧秘包|天體包|幻靈包|標準包|小丑包',
'ja': '言語|言語を選択|W/S・↑↓：移動  Enter：決定  Esc：戻る|言語を保存しました|現在の言語|決定|キャンセル|戻る|続ける|開始|ヘルプ|デッキ|難易度|ショップ|ブラインド|ボス|ジョーカー|消耗カード|カード|所持カード|全デッキ|パック|バウチャー|スコア|目標|所持金|手札|ハンド数|捨て札|レベル|役一覧|購入|売却|使用|詳細|次のラウンド|保存|読込|終了|音楽|設定|クリア|挑戦|現在|選択|カードなし|アルカナパック|天体パック|スペクトルパック|標準パック|ジョーカーパック',
'ko': '언어|언어 선택|W/S 또는 ↑↓ 이동 · Enter 확인 · Esc 취소|언어 저장됨|현재 언어|확인|취소|뒤로|계속|시작|도움말|덱|난이도|상점|블라인드|보스|조커|소모품|카드|보유 카드|전체 덱|팩|바우처|점수|목표|돈|패|핸드|버리기|레벨|포커 족보|구매|판매|사용|상세|다음 라운드|저장|불러오기|종료|음악|설정|완료|도전|현재|선택|카드 없음|아르카나 팩|천체 팩|스펙트럼 팩|표준 팩|조커 팩',
'fr': 'Langue|Choisir la langue|W/S ou ↑↓ : déplacer · Entrée : valider · Esc : retour|Langue enregistrée|Langue actuelle|Valider|Annuler|Retour|Continuer|Jouer|Aide|Paquet|Mise|Boutique|Blind|Boss|Jokers|Consommables|Cartes|Mes cartes|Paquet complet|Boosters|Bons|Score|Objectif|Argent|Main|Mains|Défausses|Niveaux|Mains de poker|Acheter|Vendre|Utiliser|Détails|Tour suivant|Sauver|Charger|Quitter|Musique|Options|Terminé|Défi|Actuel|Choisir|Aucune carte|Pack Arcana|Pack Céleste|Pack Spectral|Pack Standard|Pack Joker',
'es': 'Idioma|Elegir idioma|W/S o ↑↓: mover · Enter: aceptar · Esc: volver|Idioma guardado|Idioma actual|Aceptar|Cancelar|Volver|Continuar|Empezar|Ayuda|Baraja|Apuesta|Tienda|Ciega|Jefe|Comodines|Consumibles|Cartas|Mis cartas|Baraja completa|Sobres|Vales|Puntos|Objetivo|Dinero|Mano|Manos|Descartes|Niveles|Manos de póker|Comprar|Vender|Usar|Detalles|Siguiente ronda|Guardar|Cargar|Salir|Música|Ajustes|Superado|Desafío|Actual|Elegir|Sin cartas|Sobre Arcana|Sobre Celestial|Sobre Espectral|Sobre Estándar|Sobre Comodín',
'de': 'Sprache|Sprache wählen|W/S oder ↑↓: wählen · Enter: bestätigen · Esc: zurück|Sprache gespeichert|Aktuelle Sprache|Bestätigen|Abbrechen|Zurück|Fortsetzen|Start|Hilfe|Deck|Einsatz|Shop|Blind|Boss|Joker|Verbrauchskarten|Karten|Meine Karten|Ganzes Deck|Packs|Gutscheine|Punkte|Ziel|Geld|Hand|Hände|Abwürfe|Level|Pokerhände|Kaufen|Verkaufen|Nutzen|Details|Nächste Runde|Speichern|Laden|Beenden|Musik|Optionen|Erledigt|Herausforderung|Aktuell|Wählen|Keine Karten|Arcana-Pack|Himmels-Pack|Spektral-Pack|Standard-Pack|Joker-Pack',
'it': 'Lingua|Scegli la lingua|W/S o ↑↓: sposta · Invio: conferma · Esc: annulla|Lingua salvata|Lingua attuale|Conferma|Annulla|Indietro|Continua|Inizia|Aiuto|Mazzo|Puntata|Negozio|Blind|Boss|Jolly|Consumabili|Carte|Le mie carte|Mazzo completo|Pacchetti|Buoni|Punti|Obiettivo|Denaro|Mano|Mani|Scarti|Livelli|Mani di poker|Compra|Vendi|Usa|Dettagli|Prossimo round|Salva|Carica|Esci|Musica|Opzioni|Completato|Sfida|Attuale|Scegli|Nessuna carta|Pacco Arcana|Pacco Celestiale|Pacco Spettrale|Pacco Standard|Pacco Jolly',
'pt_BR': 'Idioma|Escolher idioma|W/S ou ↑↓: mover · Enter: confirmar · Esc: voltar|Idioma salvo|Idioma atual|Confirmar|Cancelar|Voltar|Continuar|Começar|Ajuda|Baralho|Aposta|Loja|Blind|Chefe|Curingas|Consumíveis|Cartas|Minhas cartas|Baralho completo|Pacotes|Vales|Pontos|Meta|Dinheiro|Mão|Mãos|Descartes|Níveis|Mãos de pôquer|Comprar|Vender|Usar|Detalhes|Próxima rodada|Salvar|Carregar|Sair|Música|Opções|Concluído|Desafio|Atual|Escolher|Sem cartas|Pacote Arcana|Pacote Celestial|Pacote Espectral|Pacote Padrão|Pacote Curinga',
'ru': 'Язык|Выбор языка|W/S или ↑↓: выбор · Enter: принять · Esc: назад|Язык сохранён|Текущий язык|Принять|Отмена|Назад|Продолжить|Начать|Помощь|Колода|Ставка|Магазин|Блайнд|Босс|Джокеры|Расходники|Карты|Мои карты|Вся колода|Наборы|Ваучеры|Очки|Цель|Деньги|Рука|Разыгрывания|Сбросы|Уровни|Покерные руки|Купить|Продать|Применить|Описание|Следующий раунд|Сохранить|Загрузить|Выход|Музыка|Настройки|Пройдено|Вызов|Текущий|Выбрать|Нет карт|Пакет Аркана|Небесный пакет|Спектральный пакет|Стандартный пакет|Пакет джокеров',
'nl': 'Taal|Taal kiezen|W/S of ↑↓: kiezen · Enter: bevestigen · Esc: terug|Taal opgeslagen|Huidige taal|Bevestigen|Annuleren|Terug|Doorgaan|Start|Help|Kaartspel|Inzet|Winkel|Blind|Baas|Jokers|Verbruikskaarten|Kaarten|Mijn kaarten|Hele deck|Pakketten|Vouchers|Score|Doel|Geld|Hand|Handen|Weggooien|Niveaus|Pokerhanden|Kopen|Verkopen|Gebruiken|Details|Volgende ronde|Opslaan|Laden|Afsluiten|Muziek|Instellingen|Voltooid|Uitdaging|Huidig|Kiezen|Geen kaarten|Arcana-pakket|Hemels pakket|Spectraal pakket|Standaardpakket|Jokerpakket',
'tr': 'Dil|Dil seç|W/S veya ↑↓: gez · Enter: onayla · Esc: geri|Dil kaydedildi|Geçerli dil|Onayla|İptal|Geri|Devam|Başla|Yardım|Deste|Bahis|Mağaza|Blind|Boss|Jokerler|Tüketilen kartlar|Kartlar|Kartlarım|Tüm deste|Paketler|Kuponlar|Puan|Hedef|Para|El|Eller|Iskartalar|Seviyeler|Poker elleri|Satın al|Sat|Kullan|Ayrıntı|Sonraki tur|Kaydet|Yükle|Çık|Müzik|Ayarlar|Tamamlandı|Mücadele|Geçerli|Seç|Kart yok|Arcana Paketi|Göksel Paket|Spektral Paket|Standart Paket|Joker Paketi',
'pl': 'Język|Wybierz język|W/S lub ↑↓: wybierz · Enter: zatwierdź · Esc: wróć|Zapisano język|Obecny język|Zatwierdź|Anuluj|Wróć|Kontynuuj|Start|Pomoc|Talia|Stawka|Sklep|Blind|Boss|Jokery|Karty zużywalne|Karty|Moje karty|Pełna talia|Paczki|Vouchery|Punkty|Cel|Pieniądze|Ręka|Ręce|Odrzuty|Poziomy|Układy pokerowe|Kup|Sprzedaj|Użyj|Szczegóły|Następna runda|Zapisz|Wczytaj|Wyjdź|Muzyka|Opcje|Ukończono|Wyzwanie|Obecny|Wybierz|Brak kart|Paczka Arkana|Paczka Niebiańska|Paczka Widmowa|Paczka Standardowa|Paczka Jokerów',
'ar': 'اللغة|اختيار اللغة|W/S أو ↑↓ للتنقل · Enter للتأكيد · Esc للرجوع|تم حفظ اللغة|اللغة الحالية|تأكيد|إلغاء|رجوع|متابعة|ابدأ|مساعدة|مجموعة|رهان|متجر|جولة|الزعيم|جوكر|بطاقات مستهلكة|بطاقات|بطاقاتي|المجموعة كاملة|حزم|قسائم|نقاط|الهدف|مال|يد|أيدٍ|تخلص|مستويات|تركيبات البوكر|شراء|بيع|استخدام|تفاصيل|الجولة التالية|حفظ|تحميل|خروج|موسيقى|إعدادات|مكتمل|تحدٍ|الحالي|اختيار|لا توجد بطاقات|حزمة أركانا|حزمة سماوية|حزمة طيفية|حزمة عادية|حزمة جوكر',
'hi': 'भाषा|भाषा चुनें|W/S या ↑↓ चुनें · Enter पुष्टि · Esc वापस|भाषा सहेजी गई|वर्तमान भाषा|पुष्टि|रद्द|वापस|जारी|शुरू|मदद|डेक|दाँव|दुकान|ब्लाइंड|बॉस|जोकर|उपयोग कार्ड|कार्ड|मेरे कार्ड|पूरा डेक|पैक|वाउचर|अंक|लक्ष्य|पैसा|हाथ|हाथों की संख्या|डिस्कार्ड|स्तर|पोकर हाथ|खरीदें|बेचें|उपयोग|विवरण|अगला दौर|सहेजें|लोड|बाहर|संगीत|सेटिंग|पूरा|चुनौती|वर्तमान|चुनें|कोई कार्ड नहीं|आर्काना पैक|सेलेस्टियल पैक|स्पेक्ट्रल पैक|स्टैंडर्ड पैक|जोकर पैक',
'id': 'Bahasa|Pilih bahasa|W/S atau ↑↓: pilih · Enter: terapkan · Esc: kembali|Bahasa disimpan|Bahasa aktif|Konfirmasi|Batal|Kembali|Lanjut|Mulai|Bantuan|Dek|Taruhan|Toko|Blind|Bos|Joker|Kartu pakai|Kartu|Kartu saya|Dek lengkap|Paket|Voucher|Skor|Target|Uang|Tangan|Jumlah tangan|Buang|Level|Kombinasi poker|Beli|Jual|Gunakan|Detail|Ronde berikut|Simpan|Muat|Keluar|Musik|Setelan|Selesai|Tantangan|Saat ini|Pilih|Tanpa kartu|Paket Arcana|Paket Celestial|Paket Spektral|Paket Standar|Paket Joker',
'vi': 'Ngôn ngữ|Chọn ngôn ngữ|W/S hoặc ↑↓: chọn · Enter: xác nhận · Esc: quay lại|Đã lưu ngôn ngữ|Ngôn ngữ hiện tại|Xác nhận|Hủy|Quay lại|Tiếp tục|Bắt đầu|Trợ giúp|Bộ bài|Mức cược|Cửa hàng|Blind|Trùm|Joker|Bài tiêu hao|Lá bài|Bài đang có|Toàn bộ bài|Gói|Phiếu|Điểm|Mục tiêu|Tiền|Tay bài|Lượt đánh|Lượt bỏ|Cấp|Tay poker|Mua|Bán|Dùng|Chi tiết|Vòng tiếp|Lưu|Tải|Thoát|Nhạc|Thiết lập|Đã xong|Thử thách|Hiện tại|Chọn|Không có bài|Gói Arcana|Gói Celestial|Gói Spectral|Gói thường|Gói Joker',
}
assert set(DATA)==set(LANGUAGE_NAMES)
for key,raw in DATA.items():
    values=raw.split('|')
    assert len(values)==len(KEYS), (key,len(values),len(KEYS))
TRANSLATIONS={lang:dict(zip(KEYS,raw.split('|'))) for lang,raw in DATA.items()}

# Longest first so e.g. "目标分数" is translated before "分数".
CHINESE_TERMS={
    '选择语言':'choose_language','当前语言':'selected_language',
    '整 套 牌 组':'full_deck','整套牌组':'full_deck',
    '已 持 有 小 丑 牌':'jokers','小 丑 牌':'jokers','小丑牌':'jokers',
    '已 持 有 效 果 牌':'consumables','持有效果牌':'consumables','效果牌':'consumables',
    '持有卡牌':'my_cards','我的持有卡牌':'my_cards',
    '选择牌组':'deck','当前牌组':'deck','牌组':'deck',
    '选择难度':'stake','难度':'stake',
    '商  店':'shop','商店':'shop','盲注':'blind','BOSS 战':'boss','BOSS':'boss',
    '补 充 包':'packs','补充包':'packs','奥秘包':'arcana_pack','天体包':'celestial_pack',
    '幻灵包':'spectral_pack','标准包':'standard_pack','小丑包':'buffoon_pack',
    '优 惠 券':'vouchers','优惠券':'vouchers',
    '本轮分数':'score','目标分数':'target_score','金币':'money',
    '出牌次数':'hands','弃牌次数':'discards',
    '手 牌':'hand','手牌':'hand',
    '牌 型 组 合 与 等 级':'poker_hands','牌型组合与等级':'poker_hands',
    '当前等级':'levels','等级':'levels',
    '操  作  指  南':'help','帮助':'help',
    '已完成':'completed','即将挑战':'challenge',
    '当前':'current','选择':'select',
    '出售':'sell','购买':'buy','使用':'use','详情':'details',
    '保存':'save','读取':'load','读档':'load','退出':'quit',
    '背景音乐':'music','音乐':'music',
}
PHRASE_ORDER=sorted(CHINESE_TERMS,key=len,reverse=True)
ACTIVE='zh_CN'

def set_active(locale):
    global ACTIVE
    ACTIVE=locale if locale in LANGUAGE_NAMES else 'zh_CN'

def tr(key,locale=None):
    locale=locale or ACTIVE
    return TRANSLATIONS.get(locale,TRANSLATIONS['zh_CN']).get(key,TRANSLATIONS['en'].get(key,key))

def localize(text,locale=None):
    """Translate core UI terminology while keeping rule text accurate.

    Complex Joker effects without reviewed translations remain in Chinese rather
    than being silently converted to an incorrect rule.
    """
    locale=locale or ACTIVE
    value=str(text)
    if locale=='zh_CN':return value
    for literal in PHRASE_ORDER:
        if literal in value:value=value.replace(literal,tr(CHINESE_TERMS[literal],locale))
    return value

def load_language():
    try:
        data=json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        lang=data.get('language','zh_CN')
        if lang in LANGUAGE_NAMES:return lang
    except (OSError,ValueError,TypeError,AttributeError):pass
    return 'zh_CN'

def save_language(locale):
    if locale not in LANGUAGE_NAMES:raise ValueError('Unsupported language')
    CONFIG_PATH.write_text(json.dumps({'language':locale},ensure_ascii=False,indent=2),encoding='utf-8')


def active_language():
    return ACTIVE

# Reference names and mechanical summaries; untranslated complex rule text
# is left intact rather than mistranslated. Other languages use these English
# catalog names when a language-specific game-term translation is unavailable.
DECK_DESC_EN = {
    'Red Deck':'One extra discard each round',
    'Blue Deck':'One extra hand each round',
    'Yellow Deck':'Start with an extra $10',
    'Green Deck':'Earn $2 per remaining hand and $1 per discard; no interest',
    'Black Deck':'One extra Joker slot, one fewer hand',
    'Magic Deck':'Start with Crystal Ball and two Fools',
    'Nebula Deck':'Start with Telescope; one fewer consumable slot',
    'Ghost Deck':'Spectral cards can appear in the shop; start with Hex',
    'Abandoned Deck':'No J, Q or K; start with 40 cards',
    'Checkered Deck':'Only Hearts and Spades (26 each)',
    'Zodiac Deck':'Start with three shop-related vouchers',
    'Painted Deck':'Hand size +2, Joker slots -1',
    'Anaglyph Deck':'Gain a Double Tag after defeating a Boss',
    'Plasma Deck':'Balance Chips and Mult when scoring; targets ×2',
    'Erratic Deck':'Randomize ranks and suits of the starting 52 cards',
}
STAKE_DESC_EN = {
    'White':'Standard difficulty', 'Red':'Small Blind gives no reward',
    'Green':'Score targets scale faster',
    'Black':'Eternal Jokers can appear',
    'Blue':'One fewer discard',
    'Purple':'Score targets scale much faster',
    'Orange':'Perishable Jokers can appear',
    'Gold':'Rental Jokers can appear',
}
BOSS_DESC_EN = {
    'The Hook':'Discards 2 random cards after each hand played',
    'The Ox':'Playing the specified hand type resets money to $0',
    'The House':'Starting cards are face down',
    'The Wall':'Extra-large score target',
    'The Wheel':'Some cards are drawn face down',
    'The Arm':'Lowers the level of the played poker hand',
    'The Club':'Clubs are debuffed',
    'The Fish':'Cards drawn after playing a hand are face down',
    'The Psychic':'You must play exactly 5 cards',
    'The Goad':'Spades are debuffed',
    'The Water':'No discards available',
    'The Window':'Diamonds are debuffed',
    'The Manacle':'Hand size reduced by 1',
    'The Eye':'Cannot play the same poker hand type twice',
    'The Mouth':'You may only play one hand type this round',
    'The Plant':'Face cards are debuffed',
    'The Serpent':'Draw only 3 cards after a play or discard',
    'The Pillar':'Previously played cards are debuffed',
    'The Needle':'Only one hand can be played',
    'The Head':'Hearts are debuffed',
    'The Tooth':'Lose $1 for each card played',
    'The Flint':'Base Chips and Mult are halved',
    'The Mark':'Face cards are face down',
    'Violet Vessel':'Score target multiplied by 6',
    'Crimson Heart':'Randomly debuffs one Joker each hand',
    'Amber Acorn':'Shuffles and flips Jokers at the start',
    'Verdant Leaf':'All cards are debuffed until a Joker is sold',
    'Cerulean Bell':'One card is forced into each played hand',
}

def deck_name(name,zh_name):
    return zh_name if ACTIVE.startswith('zh_') else name

def deck_desc(name,zh_description):
    return zh_description if ACTIVE.startswith('zh_') else DECK_DESC_EN.get(name,zh_description)

def stake_name(key,zh_name):
    return zh_name if ACTIVE.startswith('zh_') else key+' Stake'

def stake_desc(key,zh_description):
    return zh_description if ACTIVE.startswith('zh_') else STAKE_DESC_EN.get(key,zh_description)

def boss_name(name,zh_name):
    return zh_name if ACTIVE.startswith('zh_') else name

def boss_desc(name,zh_description):
    return zh_description if ACTIVE.startswith('zh_') else BOSS_DESC_EN.get(name,zh_description)

# Longer Chinese UI sentences with hand-reviewed English fallback. The
# interactive vocabulary in each supported locale above replaces the common
# concepts; rules/abilities which cannot be reviewed are not machine-guessed.
ENGLISH_INTERFACE_PHRASES = {
 '当 前 牌 局':'Current Run',
 '小盲注':'Small Blind',
 '大盲注':'Big Blind',
 'BOSS 战':'Boss Blind',
 '小丑槽位':'Joker slots',
 '消耗牌槽':'Consumable slots',
 '即将面对的 BOSS':'Upcoming Boss',
 '尚未显示':'Not drawn',
 '小丑牌栏已满':'Joker slots full',

 '方向键 / WASD 选择，Enter 确认':'Use arrow keys / WASD, then Enter to confirm',
 '按键操作中 · H 查看帮助':'Press a key · H for help',
 '终端窗口需要更宽敞的空间':'Please enlarge your terminal window',
 '至少 120 列 × 50 行，推荐 156 列 × 58 行':'Minimum 120 columns × 50 rows; 156 × 58 recommended',
 'Enter 进入牌组选择':'Enter: choose a deck',
 '继续游戏':'Continue game',
 '读档':'Load save',
 '返回封面':'Back to title',
 'Enter 创建新局':'Enter: new game',
 'WASD 选牌组':'WASD: choose deck',
 '方向键选难度':'Arrows: choose stake',
 'Enter 挑战':'Enter: start blind',
 'T 跳过':'T: skip',
 'E 更换 Boss':'E: reroll Boss',
 'I 持有卡牌':'I: inventory',
 'K 保存':'K: save',
 'V 语言':'V: language',
 'H 帮助':'H: help',
 '上下左右键':'Arrow keys',
 '选择奖励':'Choose reward',
 'Enter 领取':'Enter: take',
 'E 详情':'E: details',
 'Z 放弃':'Z: skip rest',
 'X 牌型等级':'X: poker hands',
 'Enter 买卖或使用效果牌':'Enter: buy/sell/use',
 'N 下一轮':'N: next round',
 'Enter 选牌':'Enter: select',
 'P 出牌':'P: play',
 'O 弃牌':'O: discard',
 '左右移动':'Move left/right',
 '选择目标':'Choose target',
 '取消目标选择':'Cancel target selection',
 '确认应用':'Confirm effect',
 'Enter 使用效果牌':'Enter: use consumable',
 'M 调整 Joker 顺序':'M: reorder Jokers',
 'M Joker 排序':'M: reorder Jokers',
 'E 查看当前焦点详情':'E: inspect focused card',
 'Enter / Esc 返回':'Enter / Esc: back',
 'Enter 返回开屏':'Enter: return to title',
 'L 读取存档':'L: load save',
 '全部已持有 Joker / 效果牌均可滚动选中':'All equipped Jokers and consumables can be selected by scrolling',
 '全部持有牌均可滚动查看':'Scroll through all owned cards',
 '可选择项目':'Selected item',
 '已售完':'Sold out',
 '离开商店':'Leave shop',
 '进入下一轮':'Next round',
 '已 持 有 小 丑 牌':'Owned Jokers',
 '已 持 有 效 果 牌':'Owned consumables',
 '单 张 卡 牌':'Single cards',
 'Enter 出售':'Enter: sell',
 'Enter 使用':'Enter: use',
 'Enter 买入 / 出售 / 使用效果':'Enter: buy / sell / use',
 '方向键 / WASD 选择':'Arrow keys / WASD: choose',
 '本 Ante 的 BOSS 能力预告':'Upcoming Boss ability',
 '未设置 Boss':'No Boss set',
 '本轮分数':'Round score',
 '完成盲注赚取金币，进入商店改善构筑':'Beat Blinds, earn money, improve your deck in the shop',
 '开始当前盲注':'Start current Blind',
 '跳过小盲注或大盲注':'Skip Small or Big Blind',
 '触发牌型由对局历史决定':'Trigger hand depends on your playing history',
 '已经在本 Ante 出过的牌将受到影响':'Cards played in this Ante will be debuffed',
 '更换下一个 BOSS（消耗 $10）':'Reroll upcoming Boss (cost $10)',
 '尚未拥有小丑牌 · 可以在商店购买':'No Jokers owned · Buy some in the shop',
 '当前选中牌型：尚未选牌':'Selected hand: no cards selected',
 '手 牌 · ':'Hand · ',
 '小 丑 牌  /  JOKERS':'JOKERS',
 '当前选中牌型：':'Selected poker hand: ',
 '剩余可选':'Picks remaining',
 '个候选':'options',
 '打开补充包并挑选奖励':'Open this pack and choose rewards',
 '购买后持续生效':'Permanent for this run',
 '出售获得 $':'Sell for $',
 '永恒小丑不可出售':'Eternal Joker cannot be sold',
 '当前奖励可按 E 查看详细说明':'Press E for a detailed reward description',
 '需要指定手牌时，Enter 会打开独立目标选择页':'Enter opens a separate target selector when needed',
 '需要选择':'Choose',
 '张手牌':'cards from your hand',
 '已选择':'Selected',
 '已选':'Selected',
 '选择效果目标':'Choose effect targets',
 '效果目标 / 手牌':'Effect targets / Hand',
 '打出':'Play',
 '弃掉':'Discard',
 '这次的牌局到此结束。':'Your run has ended.',
 '最后一手':'Last played hand',
 '小 丑 图 鉴':'Joker collection',
 '效 果 牌 图 鉴':'Consumable collection',
 '牌 型 组 合 与 等 级':'Poker Hands & Levels',
 '不构成其他牌型':'Does not form another poker hand',
 '两张点数相同':'Two cards of the same rank',
 '两组对子':'Two distinct pairs',
 '三张相同点数':'Three cards of the same rank',
 '五张点数连续':'Five consecutive ranks',
 '五张花色相同':'Five cards of the same suit',
 '三条 + 一对':'Three of a kind plus a pair',
 '四张相同点数':'Four cards of the same rank',
 '同花 + 顺子':'Flush and straight',
 '五张相同点数':'Five cards of the same rank',
 '同花 + 葫芦':'Flush and full house',
 '同花 + 五条':'Flush and five of a kind',
 '基础筹码':'Base Chips',
 '倍率':'Mult',
 '筹码':'Chips',
 '本轮':'This round',
 '牌面构成':'Card makeup',
 '尚未抽牌':'Cards not drawn yet',
 '暂无持有 Joker 或消耗牌。下一页可以查看整副牌组。':'No Jokers or consumables owned. The last page shows your complete deck.',
 '包含已购买和改造的牌':'Includes purchased and modified cards',
 '四花色':'Four suits',
 '浏览':'Scroll',
 '下一页':'Next page',
 '翻页':'Turn page',
 '选择牌组  ·  WASD 移动':'Choose deck · WASD to move',
 '选择难度  ·  方向键移动':'Choose stake · arrow keys to move',
 '难度效果':'Stake effect',
 '默认':'Default',
 '终端':'Terminal',
 '上一手得分':'Previous hand score',
 '操  作  指  南':'Controls',
 '关闭说明页，继续之前的操作':'Close details and return',
 '关闭详情，返回刚才的页面':'Close details and return',
 '当前商店优惠券':'Current shop voucher',
 '牌  面  说  明':'Card details',
 '暂无':'None',
}
# Avoid ambiguous short phrases stealing context from ability texts: first replace
# complete prompts, then translate core UI labels in the requested language.
PHRASE_ORDER_EN=sorted(ENGLISH_INTERFACE_PHRASES,key=len,reverse=True)

_old_localize=localize

def localize(text,locale=None):
    locale=locale or ACTIVE
    if locale.startswith('zh_'):
        return _old_localize(text,locale)
    value=str(text)
    for phrase in PHRASE_ORDER_EN:
        if phrase in value:value=value.replace(phrase,ENGLISH_INTERFACE_PHRASES[phrase])
    return _old_localize(value,locale)


def localize_event(message, locale=None):
    """Never leak untranslated Chinese engine notices into non-Chinese UIs.

    Localize common game feedback while avoiding speculative translations of
    unfamiliar card mechanics. For unrecognized events, show a neutral status
    instead of presenting untranslated rules as if localized.
    """
    import re
    locale=locale or ACTIVE
    raw=str(message)
    if locale.startswith('zh_'):
        return raw
    if not re.search(r'[\u3400-\u9fff]',raw):
        return raw
    # Score formulas are numbers and math with a single localized hand name.
    from .poker import HAND_ZH
    for english,zh in HAND_ZH.items():
        if raw.startswith(zh+'：'):
            return english+': '+raw[len(zh)+1:]
    patterns=(
        (r'^符印：全部 (\d+) 张手牌变成 ([♥♦♣♠])$',lambda m:f'Sigil: {m[1]} cards in hand changed to {m[2]}'),
        (r'^通灵板：全部 (\d+) 张手牌变成 (.+?)，手牌容量 -1$',lambda m:f'Ouija: {m[1]} cards changed to rank {m[2]}; hand size -1'),
        (r'^已使用效果牌：(.+)$',lambda m:'Used consumable: '+m[1]),
        (r'^已出售 Joker：(.+)$',lambda m:'Sold Joker: '+m[1]),
        (r'^从补充包选择了：(.+)$',lambda m:'Pack reward taken: '+m[1]),
        (r'^已选 (\d+) 张：.*$',lambda m:f'Selected {m[1]} cards · P: play · O: discard'),
        (r'^已保存：(.+)$',lambda m:'Saved game: '+m[1]),
        (r'^已调整 Joker 次序.*$',lambda m:'Joker order changed (scoring resolves from left to right).'),
        (r'^翠绿叶片：.*$',lambda m:'Verdant Leaf is now disabled after selling a Joker.'),
        (r'^牌局.*已开始.*$',lambda m:'Blind started. Select cards with Enter; P plays and O discards.'),
        (r'^盲注已开始.*$',lambda m:'Blind started. Enter: select · P: play · O: discard'),
        (r'^已取消使用.*$',lambda m:'Cancelled: the consumable was not spent.'),
        (r'^游戏结束.*$',lambda m:'Game over: the score target was not reached.'),
        (r'^无法计分：.*$',lambda m:'Hand disallowed by the active Boss Blind; this play scores zero.'),
        (r'^操作未执行：.*$',lambda m:'Action unavailable. Check the current game state or card requirements.'),
        (r'^未执行：.*$',lambda m:'Action unavailable. Check the current game state or card requirements.'),
        (r'^出售失败：.*$',lambda m:'Cannot sell this Joker (Eternal Jokers cannot be sold).'),
        (r'^效果未使用：.*$',lambda m:'Consumable could not be used. Check its prerequisites.'),
        (r'^目标未选：.*$',lambda m:'Cannot select that target.'),
    )
    for pattern,make in patterns:
        match=re.match(pattern,raw)
        if match:
            return make(match)
    translated=localize(raw,locale)
    if not re.search(r'[\u3400-\u9fff]',translated):
        return translated
    # A rule we cannot accurately translate must not masquerade as a localized
    # explanation; the actual card/effect details are available via E.
    return 'Game state updated. Press E on the focused card for effect details.'
