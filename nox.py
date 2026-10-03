# nox.py — NoxHub bot
import telebot
from telebot import types
import psycopg2
import psycopg2.extras
from psycopg2 import pool as pg_pool
import random, re, threading, time, datetime, sys, subprocess, os
from datetime import timedelta, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================== ТОКЕН (маскировка) ==================
_P1 = "8823737566"
_P2 = ":AAFa_k26TwoWyJy3KiZzJpWuq"
_P3 = "IcDWeSFCUU"
API_TOKEN = os.environ.get('BOT_TOKEN') or (_P1 + _P2 + _P3)

OWNER_ID = 5825717381
OWNER_USERNAME = 'NorikAmiri'
BOT_PHOTO_URL = 'https://ibb.co/jSGN6J2'
CHAT_LINK = 'https://t.me/Nox_chatik'
DATABASE_URL = os.environ.get('DATABASE_URL', '')

bot = telebot.TeleBot(API_TOKEN, threaded=True)

active_games = {}
timer_flags = {}
timer_threads = {}
invites = {}
db_lock = threading.RLock()
invite_lock = threading.Lock()
player_in_game = set()
casino_in_progress = {}
chest_cache = {}
user_list_cache = {}
unsub_attempts = {}
solo_game_stakes = {}
PROMOS_PER_PAGE = 3
CARD_NUMBER = '2200702140962171'
CHANNEL_LINK = 'https://t.me/NoxHubs'
temp_donate = {}
QUICK_BONUS_INTERVAL = 10 * 60
QUICK_BONUS_AMOUNT = 500

slot_cooldowns = {}
SLOT_COOLDOWN_SECONDS = 3
slot_user_locks = {}

BIO_BONUS_AMOUNT = 5000
BIO_BONUS_AMOUNT_BOTH = 7500
BIO_LINK_KEYWORDS = ['nox_chatik', 'noxhubbot']

# throttle для bio-check
_vip_check_cache = {}
VIP_CHECK_INTERVAL = 30

sub_check_cache = {}
SUB_CACHE_TTL = 30
BOT_ID_CACHE = {'id': None}

SLOT_WEIGHTS = [
    ('lose', 30), ('bad_lose', 32), ('fifty', 32), ('devstv', 6), ('minus2500', 1),
    ('kiwi', 34), ('cherry', 30), ('strawberry', 21), ('clover', 10), ('seven', 6),
    ('new_1_2', 8), ('new_5', 1), ('free10', 0.3), ('diamond', 0.3),
    ('super_jackpot', 0.0000001), ('neutral', 9),
]
SLOT_SYMBOLS = {
    'kiwi': ('5215458128463682363', '🥝'), 'cherry': ('5791951647072590102', '🍒'),
    'strawberry': ('5794330032457389446', '🍓'), 'clover': ('6050784754494606982', '🍀'),
    'seven': ('6035165663541072563', '7️⃣'), 'diamond': ('5967766687385129994', '💎'),
    'super_jackpot': ('6046225208623238566', '💎'), 'free10': ('5285480556543373770', '🎁'),
    'new_1_2': ('5262508344140119992', '✨'), 'new_5': ('5355115746076672241', '⭐'),
    'fifty': ('5456173242765034256', '⚖️'), 'devstv': ('5211025120918785460', '💀'),
    'minus2500': ('5415718791185179701', '💀'), 'bad_lose': ('5291842511210304612', '💀'),
    'neutral': ('5202177750282019573', '🖼️'),
}
SLOT_MULT = {'cherry': 2.0, 'seven': 3.0, 'diamond': 10.0, 'strawberry': 2.5, 'kiwi': 1.5,
             'new_1_2': 1.2, 'new_5': 5.0, 'super_jackpot': 100.0, 'fifty': 0.5}
CLOVER_MIN_BALANCE = 500
FREE_SPINS_COUNT = 10
FREE_SPIN_INTERVAL = 3


def get_slot_lock(uid):
    with invite_lock:
        if uid not in slot_user_locks:
            slot_user_locks[uid] = threading.Lock()
        return slot_user_locks[uid]


def _slot_total_weight():
    return sum(w for _, w in SLOT_WEIGHTS)


def roll_slot_outcome(user_balance=0):
    total = _slot_total_weight()
    r = random.random() * total
    acc = 0.0
    for name, w in SLOT_WEIGHTS:
        acc += w
        if r < acc:
            if name == 'clover' and user_balance <= CLOVER_MIN_BALANCE:
                return 'lose'
            return name
    return 'lose'


def emo_tag(emoji_id, fallback):
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


def strip_custom_emojis(text):
    if not text:
        return text
    return re.sub(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', r'\1', text, flags=re.DOTALL)


def get_bot_id():
    if BOT_ID_CACHE['id'] is None:
        try:
            BOT_ID_CACHE['id'] = bot.get_me().id
        except Exception:
            return None
    return BOT_ID_CACHE['id']


# ================== ЭМОДЗИ ==================
EMO_PROFILE = '<tg-emoji emoji-id="5416125589012636561">👤</tg-emoji>'
EMO_DONATE = '<tg-emoji emoji-id="5354968347094062313">💳</tg-emoji>'
EMO_DICE = '<tg-emoji emoji-id="5280816565657300091">🎲</tg-emoji>'
EMO_ADMIN = '<tg-emoji emoji-id="6129805886383723340">👑</tg-emoji>'
EMO_PROMO = '<tg-emoji emoji-id="5285423837205260312">🎟</tg-emoji>'
EMO_MINE = '<tg-emoji emoji-id="5276032951342088188">💣</tg-emoji>'
EMO_SAFE = '<tg-emoji emoji-id="5224400190244401421">✅</tg-emoji>'
EMO_FLOOR = '<tg-emoji emoji-id="5213071346417812800">🏢</tg-emoji>'
EMO_NOX = '<tg-emoji emoji-id="5274165555396390084">💰</tg-emoji>'
EMO_GOLDTEXT = '<tg-emoji emoji-id="5253711426484204035">💰</tg-emoji>'
EMO_MULT = '<tg-emoji emoji-id="5469778140085632236">📈</tg-emoji>'
EMO_TROPHY = '<tg-emoji emoji-id="5244590801438138696">🏆</tg-emoji>'
EMO_CROWN = '<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji>'
EMO_CANCEL = '<tg-emoji emoji-id="4990425769416065984">❌</tg-emoji>'
EMO_BACK = '<tg-emoji emoji-id="5348534812502159476">🔙</tg-emoji>'
EMO_CHANNEL = '<tg-emoji emoji-id="5327938120740523910">📢</tg-emoji>'
EMO_RULES = '<tg-emoji emoji-id="5262878819429141746">📖</tg-emoji>'
EMO_SUPPORT = '<tg-emoji emoji-id="5323261373801571717">🆘</tg-emoji>'
EMO_RUBLES = '<tg-emoji emoji-id="5463002283715349737">💳</tg-emoji>'
EMO_STARS = '<tg-emoji emoji-id="6008353471202333128">⭐</tg-emoji>'
EMO_INPUT = '<tg-emoji emoji-id="5314674784989098261">✍️</tg-emoji>'
EMO_ACCEPT = '<tg-emoji emoji-id="5370908873400020056">⚔️</tg-emoji>'
EMO_ROCK = '<tg-emoji emoji-id="5269640498112378277">🪨</tg-emoji>'
EMO_SCISSORS = '<tg-emoji emoji-id="5269616738353300957">✂️</tg-emoji>'
EMO_PAPER = '<tg-emoji emoji-id="5267118828323616839">📄</tg-emoji>'
EMO_ROULETTE = '<tg-emoji emoji-id="5222378729526811041">🔫</tg-emoji>'
EMO_EAGLE = '<tg-emoji emoji-id="5269254848703902904">🦅</tg-emoji>'
EMO_CHEST = '<tg-emoji emoji-id="5767355610613944397">📦</tg-emoji>'
EMO_LOCK = '<tg-emoji emoji-id="5836690092306992715">🔒</tg-emoji>'
EMO_SKULL = '<tg-emoji emoji-id="5379930048478330552">💀</tg-emoji>'
EMO_GOLD = '<tg-emoji emoji-id="5445256208992718797">💰</tg-emoji>'
EMO_GOLD2 = '<tg-emoji emoji-id="5208740833972478563">💰</tg-emoji>'
EMO_BONUS = '<tg-emoji emoji-id="5321280470460145769">🎁</tg-emoji>'
EMO_TIMER = '<tg-emoji emoji-id="4949530697141322852">⏱️</tg-emoji>'
EMO_WELCOME = '<tg-emoji emoji-id="5204240498520236976">👋</tg-emoji>'
EMO_REPORT = '<tg-emoji emoji-id="5406936308914333383">📩</tg-emoji>'
EMO_MUTE = '<tg-emoji emoji-id="5434072951672558669">🔇</tg-emoji>'
EMO_MODS = '<tg-emoji emoji-id="5985532304208957021">🛡️</tg-emoji>'
EMO_SLOTS = '<tg-emoji emoji-id="5384509325429463744">🎰</tg-emoji>'
EMO_SURRENDER = '<tg-emoji emoji-id="5411534277563150683">🏳️</tg-emoji>'
EMO_CHERRY = '<tg-emoji emoji-id="5791951647072590102">🍒</tg-emoji>'
EMO_DIAMOND = '<tg-emoji emoji-id="5967766687385129994">💎</tg-emoji>'
EMO_KIWI = '<tg-emoji emoji-id="5215458128463682363">🥝</tg-emoji>'
EMO_NUMBER = '<tg-emoji emoji-id="6323436631428695574">🔢</tg-emoji>'
EMO_DOWN = '<tg-emoji emoji-id="6010464967319359998">👇</tg-emoji>'
EMO_BULB = '<tg-emoji emoji-id="5422439311196834318">💡</tg-emoji>'
EMO_FIRE = '<tg-emoji emoji-id="5424972470023104089">🔥</tg-emoji>'
EMO_SOLO_HEADER = '<tg-emoji emoji-id="6001198270435563383">🎮</tg-emoji>'
EMO_PVP_HEADER = '<tg-emoji emoji-id="5879483295313433344">⚔️</tg-emoji>'
EMO_TTT_X = '<tg-emoji emoji-id="5438194320685414000">❌</tg-emoji>'
EMO_TTT_O = '<tg-emoji emoji-id="5393109606597685796">⭕</tg-emoji>'
EMO_TTT_INVITE = '<tg-emoji emoji-id="5359419191638114278">🎮</tg-emoji>'
EMO_CHAT = '<tg-emoji emoji-id="5235814241927181048">💬</tg-emoji>'
EMO_VS = '<tg-emoji emoji-id="5354932922203782306">⚔️</tg-emoji>'
EMO_BOOM = '<tg-emoji emoji-id="5424972470023104089">🔥</tg-emoji>'
EMO_HANDSHAKE = '<tg-emoji emoji-id="5370908873400020056">🤝</tg-emoji>'
EMO_VIP = '<tg-emoji emoji-id="5996899742611672774">🔶</tg-emoji>'
# Новые VIP-эмодзи
EMO_VIP_7500 = '<tg-emoji emoji-id="5406891929017271647">🔶</tg-emoji>'
EMO_VIP_5000 = '<tg-emoji emoji-id="5251215200081698759">🔶</tg-emoji>'
EMO_VIP_MILLION = '<tg-emoji emoji-id="5271925605397443302">💎</tg-emoji>'

EMO_DIV_SOLO = '<tg-emoji emoji-id="5226554936682100372">➖</tg-emoji>'
EMO_DIV_PVP = '<tg-emoji emoji-id="5318883801399567148">➖</tg-emoji>'
DIV_SOLO_LINE = (EMO_DIV_SOLO + ' ') * 12
DIV_PVP_LINE = (EMO_DIV_PVP + ' ') * 12

ICO_PROFILE = '5416125589012636561'
ICO_DONATE = '5354968347094062313'
ICO_CHANNEL = '5327938120740523910'
ICO_RULES = '5262878819429141746'
ICO_SUPPORT = '5323261373801571717'
ICO_BACK = '5348534812502159476'
ICO_RUBLES = '5463002283715349737'
ICO_STARS = '6008353471202333128'
ICO_INPUT = '5314674784989098261'
ICO_ACCEPT = '5370908873400020056'
ICO_ROCK = '5269640498112378277'
ICO_SCISSORS = '5269616738353300957'
ICO_PAPER = '5267118828323616839'
ICO_ROULETTE = '5222378729526811041'
ICO_EAGLE = '5269254848703902904'
ICO_CHEST = '5767355610613944397'
ICO_LOCK = '5836690092306992715'
ICO_SKULL = '5379930048478330552'
ICO_GOLD = '5445256208992718797'
ICO_GOLD2 = '5208740833972478563'
ICO_GOLD_BTN = '5253711426484204035'
ICO_SURRENDER = '5411534277563150683'
ICO_CANCEL = '4990425769416065984'
ICO_ADMIN = '6129805886383723340'
ICO_PROMO = '5285423837205260312'
ICO_SAFE = '5224400190244401421'
ICO_MINE = '5276032951342088188'
ICO_CHAT = '5235814241927181048'
ICO_TTT_X = '5438194320685414000'
ICO_TTT_O = '5393109606597685796'
ICO_TTT_INVITE = '5359419191638114278'
ICO_FLOOR = '5213071346417812800'
ICO_SLOTS = '5384509325429463744'
ICO_BONUS_ICO = '5321280470460145769'
ICO_BULB = '5422439311196834318'
ICO_TIMER = '4949530697141322852'
ICO_PVP_HEADER = '5879483295313433344'
ICO_SOLO_HEADER = '6001198270435563383'
ICO_DICE = '5280816565657300091'
ICO_NUMBER = '6323436631428695574'
ICO_VS = '5354932922203782306'
ICO_DIAMOND = '5967766687385129994'
ICO_VIP = '5996899742611672774'


def btn(text, callback_data=None, url=None, style=None, icon=None):
    kwargs = {'text': text}
    if callback_data:
        kwargs['callback_data'] = callback_data
    if url:
        kwargs['url'] = url
    if style:
        kwargs['style'] = style
    if icon:
        kwargs['icon_custom_emoji_id'] = icon
    try:
        return types.InlineKeyboardButton(**kwargs)
    except TypeError:
        kwargs.pop('style', None)
        kwargs.pop('icon_custom_emoji_id', None)
        return types.InlineKeyboardButton(**kwargs)


def safe_send(chat_id, text, **kwargs):
    for attempt in range(3):
        try:
            return bot.send_message(chat_id, text, **kwargs)
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 429:
                ra = 3
                try:
                    if hasattr(e, 'result_json') and e.result_json:
                        ra = e.result_json.get('parameters', {}).get('retry_after', 3)
                except Exception:
                    pass
                time.sleep(ra + 1)
                continue
            if e.error_code == 400:
                clean = strip_custom_emojis(text)
                try:
                    kw = dict(kwargs)
                    kw.pop('parse_mode', None)
                    return bot.send_message(chat_id, clean, **kw)
                except Exception:
                    pass
            print(f"[send ERR] {e.error_code}: {e}")
            return None
        except Exception as e:
            print(f"[send EXC] {type(e).__name__}: {e}")
            return None
    return None


def safe_edit(chat_id, message_id, text, **kwargs):
    for attempt in range(3):
        try:
            return bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, **kwargs)
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 429:
                ra = 3
                try:
                    if hasattr(e, 'result_json') and e.result_json:
                        ra = e.result_json.get('parameters', {}).get('retry_after', 3)
                except Exception:
                    pass
                time.sleep(ra + 1)
                continue
            if e.error_code == 400:
                clean = strip_custom_emojis(text)
                try:
                    kw = dict(kwargs)
                    kw.pop('parse_mode', None)
                    return bot.edit_message_text(clean, chat_id=chat_id, message_id=message_id, **kw)
                except Exception:
                    pass
            if e.error_code == 400 and ('not modified' in str(e) or 'no text' in str(e)):
                try:
                    return bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=message_id, **kwargs)
                except Exception:
                    try:
                        bot.delete_message(chat_id, message_id)
                    except Exception:
                        pass
                    return safe_send(chat_id, text, **kwargs)
            return None
        except Exception as e:
            print(f"[edit EXC] {type(e).__name__}: {e}")
            return None
    return None


def safe_answer(call_id, text=None, show_alert=False):
    try:
        if text:
            bot.answer_callback_query(call_id, text, show_alert=show_alert)
        else:
            bot.answer_callback_query(call_id)
    except Exception:
        pass


def send_slot_result(chat_id, text):
    result = safe_send(chat_id, text, parse_mode='HTML')
    if result is not None:
        return result
    clean = strip_custom_emojis(text)
    try:
        return bot.send_message(chat_id, clean)
    except Exception as e:
        print(f"[SLOT FALLBACK ERR] {e}")
        try:
            return bot.send_message(chat_id, clean, parse_mode=None)
        except Exception as e2:
            print(f"[SLOT FALLBACK2 ERR] {e2}")
            return None


# ================== ПУЛ ==================
_db_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    global _db_pool
    if _db_pool is None:
        with _pool_lock:
            if _db_pool is None:
                _db_pool = pg_pool.SimpleConnectionPool(2, 30, DATABASE_URL)
    return _db_pool


class PooledConn:
    __slots__ = ('conn', 'pool', '_closed')

    def __init__(self):
        self.pool = _get_pool()
        self.conn = self.pool.getconn()
        self._closed = False

    def __getattr__(self, name):
        return getattr(self.conn, name)

    def close(self):
        if not self._closed:
            self._closed = True
            try:
                if self.conn.closed:
                    self.pool.putconn(self.conn, close=True)
                else:
                    self.pool.putconn(self.conn)
            except Exception:
                pass


def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL не задан!")
    return PooledConn()


def db_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def column_exists(cursor, table, column):
    cursor.execute("""SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND column_name = %s""", (table, column))
    return cursor.fetchone() is not None


def init_db():
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY, username TEXT, first_name TEXT,
            balance BIGINT DEFAULT 2000, last_bonus BIGINT DEFAULT 0,
            current_streak INTEGER DEFAULT 0, max_streak INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0, last_bonus_date TEXT DEFAULT NULL,
            last_quick_bonus TEXT DEFAULT NULL,
            bio_bonus_active INTEGER DEFAULT 0,
            bio_bonus_last_date TEXT DEFAULT NULL,
            vip_amount BIGINT DEFAULT 0)''')
        for col, ddl in [
            ('banned', 'ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0'),
            ('last_bonus_date', 'ALTER TABLE users ADD COLUMN last_bonus_date TEXT DEFAULT NULL'),
            ('last_quick_bonus', 'ALTER TABLE users ADD COLUMN last_quick_bonus TEXT DEFAULT NULL'),
            ('bio_bonus_active', 'ALTER TABLE users ADD COLUMN bio_bonus_active INTEGER DEFAULT 0'),
            ('bio_bonus_last_date', 'ALTER TABLE users ADD COLUMN bio_bonus_last_date TEXT DEFAULT NULL'),
            ('vip_amount', 'ALTER TABLE users ADD COLUMN vip_amount BIGINT DEFAULT 0'),
        ]:
            if not column_exists(cursor, 'users', col):
                cursor.execute(ddl)
        cursor.execute('''CREATE TABLE IF NOT EXISTS game_stats (
            user_id BIGINT, game_type TEXT, wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, game_type))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS promos (code TEXT PRIMARY KEY, reward BIGINT,
            max_uses INTEGER, current_uses INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS promo_history (code TEXT, user_id BIGINT,
            activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (code, user_id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS chats (chat_id BIGINT PRIMARY KEY,
            chat_title TEXT, sub_required INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS required_subscriptions (
            id SERIAL PRIMARY KEY, chat_id BIGINT UNIQUE, type TEXT, link TEXT, title TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_subscriptions (
            user_id BIGINT, chat_id BIGINT, confirmed INTEGER DEFAULT 0, PRIMARY KEY (user_id, chat_id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS moderators (user_id BIGINT PRIMARY KEY,
            role TEXT DEFAULT 'moderator', added_by BIGINT, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS co_owners (user_id BIGINT PRIMARY KEY,
            added_by BIGINT, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('INSERT INTO moderators (user_id, role, added_by) VALUES (%s,%s,%s) ON CONFLICT (user_id) DO NOTHING',
                       (OWNER_ID, 'owner', OWNER_ID))
        conn.commit()
        conn.close()


# ---------- BIO / VIP ----------

def _bio_contains_keyword(text):
    if not text:
        return False
    t = text.lower()
    return any(kw in t for kw in BIO_LINK_KEYWORDS)


def check_user_bio_link_detailed(user_id, username=None, first_name=None):
    """Возвращает (has_link, request_ok)."""
    try:
        chat = bot.get_chat(user_id)
        bio = getattr(chat, 'bio', None) or ''
        un = getattr(chat, 'username', None) or ''
        fn = getattr(chat, 'first_name', None) or ''
        result = _bio_contains_keyword(bio) or _bio_contains_keyword(un) or _bio_contains_keyword(fn)
        if not result and username and _bio_contains_keyword(username):
            result = True
        if not result and first_name and _bio_contains_keyword(first_name):
            result = True
        return (result, True)
    except Exception as e:
        print(f"[BIO CHECK ERR] {e}")
        return (False, False)


def check_user_bio_link(user_id, username=None):
    r, _ = check_user_bio_link_detailed(user_id, username)
    return r


def check_vip_links(user_id, username=None, first_name=None):
    """Возвращает (has_bio, has_nick)."""
    try:
        chat = bot.get_chat(user_id)
        bio = getattr(chat, 'bio', None) or ''
        un = getattr(chat, 'username', None) or ''
        fn = getattr(chat, 'first_name', None) or ''
        has_bio = _bio_contains_keyword(bio)
        has_nick = _bio_contains_keyword(un) or _bio_contains_keyword(fn)
        if not has_nick and username and _bio_contains_keyword(username):
            has_nick = True
        if not has_nick and first_name and _bio_contains_keyword(first_name):
            has_nick = True
        return has_bio, has_nick
    except Exception as e:
        print(f"[VIP CHECK ERR] {e}")
        return False, False


def get_bio_bonus_remaining_seconds(user):
    if not user['bio_bonus_active']:
        return 0
    last = user['bio_bonus_last_date']
    today = get_moscow_date()
    if last != today:
        return 0
    now_msk = datetime.datetime.now(timezone(timedelta(hours=3)))
    next_midnight = (now_msk + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(0, int((next_midnight - now_msk).total_seconds()))


def format_bio_bonus_time(seconds):
    if seconds <= 0:
        return "готово"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if h > 0:
        return f"{h}ч {m}м"
    return f"{m}м"


def activate_vip(uid, chat_id, message=None):
    """
    VIP-логика:
    - Ссылка и в био, и в нике → 7500 (эмодзи 5406891929017271647)
    - Ссылка только в одном месте → 5000 (эмодзи 5251215200081698759)
    - Нет ссылки → снимаем VIP и списываем текущую сумму
    - 1 миллион баланса → доп. эмодзи 5271925605397443302
    """
    try:
        user = get_or_create_user(uid, "", "")
        uname = message.from_user.username if (message and getattr(message, 'from_user', None)) else None
        fname = message.from_user.first_name if (message and getattr(message, 'from_user', None)) else None
        has_bio, has_nick = check_vip_links(uid, uname, fname)

        if has_bio and has_nick:
            new_amount = BIO_BONUS_AMOUNT_BOTH
        elif has_bio or has_nick:
            new_amount = BIO_BONUS_AMOUNT
        else:
            new_amount = 0

        was_active = user['bio_bonus_active'] == 1
        old_amount = user.get('vip_amount', 0) or 0
        today = get_moscow_date()

        if new_amount > 0:
            if not was_active:
                with db_lock:
                    conn = get_db_connection()
                    cursor = db_cursor(conn)
                    cursor.execute(
                        'UPDATE users SET bio_bonus_active = 1, vip_amount = %s, bio_bonus_last_date = %s, '
                        'balance = balance + %s WHERE user_id = %s',
                        (new_amount, today, new_amount, uid))
                    conn.commit()
                    conn.close()
                name = ""
                if message and getattr(message, 'from_user', None):
                    name = (message.from_user.first_name or message.from_user.username or "Пользователь")
                else:
                    u = get_or_create_user(uid, "", "")
                    name = u['first_name'] or u['username'] or "Пользователь"
                emo = EMO_VIP_7500 if new_amount >= BIO_BONUS_AMOUNT_BOTH else EMO_VIP_5000
                safe_send(chat_id,
                          f"{EMO_VIP} <b>VIP-СТАТУС ПОДКЛЮЧЕН!</b> {EMO_VIP}\n\n"
                          f"{EMO_SAFE} Пользователь: <b>{name}</b>\n"
                          f"{EMO_NOX} Сразу начислено: <b>+{new_amount:,}</b> ноксов!\n"
                          f"{emo} Рядом с его ником появился <b>VIP-значок</b>",
                          parse_mode='HTML')
                return True
            elif old_amount != new_amount:
                diff = new_amount - old_amount
                with db_lock:
                    conn = get_db_connection()
                    cursor = db_cursor(conn)
                    cursor.execute(
                        'UPDATE users SET vip_amount = %s, balance = balance + %s WHERE user_id = %s',
                        (new_amount, diff, uid))
                    conn.commit()
                    conn.close()
                if diff > 0:
                    safe_send(chat_id,
                              f"{EMO_VIP} {get_user_display_by_id(uid)} обновил VIP-статус!\n"
                              f"{EMO_NOX} Начислено: <b>+{diff:,}</b>\n"
                              f"{EMO_BULB} Теперь: <b>{new_amount:,}</b> в день",
                              parse_mode='HTML')
                else:
                    safe_send(chat_id,
                              f"{EMO_CANCEL} {get_user_display_by_id(uid)} изменил ссылку!\n"
                              f"{EMO_NOX} Списано: <b>{abs(diff):,}</b>\n"
                              f"{EMO_BULB} Теперь: <b>{new_amount:,}</b> в день",
                              parse_mode='HTML')
                return True
            elif user['bio_bonus_last_date'] != today:
                with db_lock:
                    conn = get_db_connection()
                    cursor = db_cursor(conn)
                    cursor.execute('UPDATE users SET balance = balance + %s, bio_bonus_last_date = %s WHERE user_id = %s',
                                   (old_amount, today, uid))
                    conn.commit()
                    conn.close()
                safe_send(chat_id,
                          f"{EMO_VIP} {get_user_display_by_id(uid)} получил <b>+{old_amount:,} {EMO_NOX}</b> "
                          f"за VIP-статус! 🎉",
                          parse_mode='HTML')
                return True
        else:
            if was_active:
                with db_lock:
                    conn = get_db_connection()
                    cursor = db_cursor(conn)
                    cursor.execute(
                        'UPDATE users SET bio_bonus_active = 0, vip_amount = 0, bio_bonus_last_date = NULL, '
                        'balance = balance - %s WHERE user_id = %s',
                        (old_amount, uid))
                    conn.commit()
                    conn.close()
                safe_send(chat_id,
                          f"{EMO_CANCEL} {get_user_display_by_id(uid)} убрал ссылку из профиля!\n"
                          f"{EMO_VIP} VIP-статус снят\n"
                          f"{EMO_NOX} Списано: <b>-{old_amount:,}</b>",
                          parse_mode='HTML')
            return False
    except Exception as e:
        print(f"[ACTIVATE VIP ERR] {e}")
        return False


# ---------- CO OWNERS ----------

def is_co_owner(user_id):
    if user_id == OWNER_ID:
        return True
    try:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('SELECT 1 FROM co_owners WHERE user_id = %s', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row is not None
    except Exception:
        return user_id == OWNER_ID


def add_co_owner(user_id, added_by):
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('INSERT INTO co_owners (user_id, added_by) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING',
                       (user_id, added_by))
        conn.commit()
        conn.close()


def remove_co_owner(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('DELETE FROM co_owners WHERE user_id = %s', (user_id,))
        conn.commit()
        conn.close()


def get_co_owners():
    conn = get_db_connection()
    cursor = db_cursor(conn)
    cursor.execute('SELECT user_id FROM co_owners ORDER BY added_at')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- ОБЩИЕ ----------

def _build_vip_suffix(vip_active, vip_amount, balance):
    suffix = ''
    if vip_active:
        if vip_amount >= BIO_BONUS_AMOUNT_BOTH:
            suffix += f' {EMO_VIP_7500}'
        elif vip_amount > 0:
            suffix += f' {EMO_VIP_5000}'
    if balance >= 1_000_000:
        suffix += f' {EMO_VIP_MILLION}'
    return suffix


def get_user_display(user):
    try:
        uid = None
        name = None
        vip_active = False
        vip_amount = 0
        balance = 0
        got_all = False

        if hasattr(user, 'id') and hasattr(user, 'first_name'):
            uid = user.id
            name = (getattr(user, 'first_name', '') or '').strip() or (getattr(user, 'username', '') or '').strip()
        else:
            try:
                uid = user['user_id']
                fn = user['first_name'] or ''
                un = user['username'] or ''
                name = fn.strip() or un.strip()
                try:
                    vip_active = user['bio_bonus_active'] == 1
                    vip_amount = user['vip_amount'] or 0
                    balance = user['balance'] or 0
                    got_all = True
                except (KeyError, TypeError, IndexError):
                    pass
            except (KeyError, TypeError, IndexError):
                try:
                    uid = user.get('user_id')
                    name = ((user.get('first_name') or '').strip() or (user.get('username') or '').strip())
                    vip_active = user.get('bio_bonus_active', 0) == 1
                    vip_amount = user.get('vip_amount', 0) or 0
                    balance = user.get('balance', 0) or 0
                    got_all = True
                except Exception:
                    pass

        if uid and not got_all:
            try:
                conn = get_db_connection()
                cursor = db_cursor(conn)
                cursor.execute('SELECT first_name, username, bio_bonus_active, vip_amount, balance FROM users WHERE user_id = %s', (uid,))
                row = cursor.fetchone()
                conn.close()
                if row:
                    if not name:
                        name = (row['first_name'] or '').strip() or (row['username'] or '').strip()
                    vip_active = (row['bio_bonus_active'] == 1)
                    vip_amount = row['vip_amount'] or 0
                    balance = row['balance'] or 0
            except Exception as e:
                print(f"[DISPLAY DB ERR] {e}")

        if not uid:
            return "Пользователь"
        if not name:
            name = f"id{uid}"
        link = f'<a href="tg://user?id={uid}">{name}</a>'
        return link + _build_vip_suffix(vip_active, vip_amount, balance)
    except Exception as e:
        print(f"[DISPLAY ERR] {e}")
        return "Пользователь"


def get_user_display_by_id(user_id):
    user = get_or_create_user(user_id, "", "")
    return get_user_display(user)


def get_or_create_user(user_id, username, first_name):
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.execute('INSERT INTO users (user_id, username, first_name, balance, banned, last_bonus_date) '
                           'VALUES (%s, %s, %s, %s, 0, NULL)', (user_id, username, first_name, 2000))
            for g in ['dice', 'rps', 'ttt', 'mines', 'number']:
                cursor.execute('''INSERT INTO game_stats (user_id, game_type, wins, losses) VALUES (%s, %s, 0, 0)
                    ON CONFLICT (user_id, game_type) DO NOTHING''', (user_id, g))
            conn.commit()
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
        else:
            if username or first_name:
                cursor.execute("UPDATE users SET username = COALESCE(NULLIF(%s, ''), username), "
                               "first_name = COALESCE(NULLIF(%s, ''), first_name) WHERE user_id = %s",
                               (username, first_name, user_id))
            for g in ['dice', 'rps', 'ttt', 'mines', 'number']:
                cursor.execute('''INSERT INTO game_stats (user_id, game_type, wins, losses) VALUES (%s, %s, 0, 0)
                    ON CONFLICT (user_id, game_type) DO NOTHING''', (user_id, g))
            conn.commit()
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
        conn.close()
        return user


def is_banned(user_id):
    conn = get_db_connection()
    cursor = db_cursor(conn)
    cursor.execute('SELECT banned FROM users WHERE user_id = %s', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row and row['banned'] == 1


def get_all_users():
    conn = get_db_connection()
    cursor = db_cursor(conn)
    cursor.execute('SELECT user_id, username, first_name, balance, bio_bonus_active, vip_amount FROM users ORDER BY balance DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_chats():
    conn = get_db_connection()
    cursor = db_cursor(conn)
    cursor.execute('SELECT chat_id, chat_title, sub_required FROM chats')
    rows = cursor.fetchall()
    conn.close()
    return rows


def add_chat(chat_id, title):
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('INSERT INTO chats (chat_id, chat_title) VALUES (%s, %s) '
                       'ON CONFLICT (chat_id) DO UPDATE SET chat_title = EXCLUDED.chat_title', (chat_id, title))
        conn.commit()
        conn.close()


def update_balance(user_id, amount):
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('UPDATE users SET balance = balance + %s WHERE user_id = %s', (amount, user_id))
        conn.commit()
        conn.close()


def set_balance(user_id, amount):
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('UPDATE users SET balance = %s WHERE user_id = %s', (amount, user_id))
        conn.commit()
        conn.close()


def update_game_stats(user_id, game_type, is_win):
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        if is_win:
            cursor.execute('UPDATE game_stats SET wins = wins + 1 WHERE user_id = %s AND game_type = %s', (user_id, game_type))
        else:
            cursor.execute('UPDATE game_stats SET losses = losses + 1 WHERE user_id = %s AND game_type = %s', (user_id, game_type))
        conn.commit()
        conn.close()


def get_all_stats(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        for g in ['dice', 'rps', 'ttt', 'mines', 'number']:
            cursor.execute('''INSERT INTO game_stats (user_id, game_type, wins, losses) VALUES (%s, %s, 0, 0)
                ON CONFLICT (user_id, game_type) DO NOTHING''', (user_id, g))
        conn.commit()
        cursor.execute('SELECT * FROM game_stats WHERE user_id = %s', (user_id,))
        rows = cursor.fetchall()
        conn.close()
    stats = {}
    names = {'dice': f'{EMO_DICE} Кости 1на1', 'rps': f'{EMO_ROCK} Камень-Ножницы-Бумага',
             'ttt': f'{EMO_TTT_INVITE} Крестики-Нолики 3х3', 'mines': f'{EMO_MINE} Минное поле 5x5',
             'number': f'{EMO_NUMBER} Угадай число'}
    for row in rows:
        g = row['game_type']
        if g in names:
            w, l = row['wins'], row['losses']
            t = w + l
            wr = 0.0 if t == 0 else round(((w - l) / t) * 100, 1)
            stats[g] = {'name': names[g], 'wins': w, 'losses': l, 'winrate': wr}
    for g in ['dice', 'rps', 'ttt', 'mines', 'number']:
        if g not in stats:
            stats[g] = {'name': names[g], 'wins': 0, 'losses': 0, 'winrate': 0.0}
    return stats


def update_streak(user_id, is_win, stake=0):
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('SELECT current_streak, max_streak FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        if not res:
            conn.close()
            return
        cur, mx = res['current_streak'], res['max_streak']
        if is_win:
            if stake >= 1000:
                cur += 1
                if cur > mx:
                    mx = cur
        else:
            cur = 0
        cursor.execute('UPDATE users SET current_streak = %s, max_streak = %s WHERE user_id = %s', (cur, mx, user_id))
        conn.commit()
        conn.close()


def check_banned(user_id, chat_id):
    if is_banned(user_id):
        user = get_or_create_user(user_id, "", "")
        display = get_user_display(user)
        safe_send(chat_id, f"{EMO_CANCEL} Вы забанены, {display}.", parse_mode='HTML')
        return True
    return False


def check_pm_game(message):
    if message.chat.type == 'private':
        safe_send(message.chat.id, f"{EMO_SOLO_HEADER} <b>Игры только в чате!</b>\n\n👉 @Nox_chatik", parse_mode='HTML')
        return True
    return False


def get_moscow_date():
    return datetime.datetime.now(timezone(timedelta(hours=3))).strftime('%Y-%m-%d')


def get_quick_bonus_remaining(user):
    if not user['last_quick_bonus']:
        return 0
    try:
        last = datetime.datetime.fromisoformat(str(user['last_quick_bonus']))
    except Exception:
        return 0
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    return max(0, int(QUICK_BONUS_INTERVAL - (now - last).total_seconds()))


def format_time(s):
    s = int(s)
    m = s // 60
    ss = s % 60
    return f"{m}м {ss}с" if m > 0 else f"{ss}с"


def build_balance_text(user):
    return f"{get_user_display(user)}\n{EMO_NOX} <code>{user['balance']:,}</code> ноксов"


def get_chat_link(chat_id):
    try:
        chat = bot.get_chat(chat_id)
        if getattr(chat, 'username', None):
            return f"https://t.me/{chat.username}"
    except Exception:
        pass
    try:
        return bot.export_chat_invite_link(chat_id)
    except Exception:
        return None


# ---------- ПОДПИСКИ ----------

def get_required_subscriptions():
    conn = get_db_connection()
    cursor = db_cursor(conn)
    cursor.execute('SELECT id, chat_id, type, link, title FROM required_subscriptions')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_required_subscription(chat_id, type_, link, title):
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        try:
            bot.get_chat(chat_id)
        except Exception as e:
            conn.close()
            raise Exception(f"Err: {e}")
        try:
            cursor.execute('INSERT INTO required_subscriptions (chat_id, type, link, title) VALUES (%s, %s, %s, %s) '
                           'ON CONFLICT (chat_id) DO NOTHING', (chat_id, type_, link, title))
            cursor.execute('DELETE FROM user_subscriptions WHERE chat_id = %s', (chat_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            raise Exception(f"Err: {e}")
        conn.close()


def remove_required_subscription(sub_id):
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        try:
            cursor.execute('SELECT chat_id FROM required_subscriptions WHERE id = %s', (sub_id,))
            row = cursor.fetchone()
            cid = row['chat_id'] if row else None
            cursor.execute('DELETE FROM required_subscriptions WHERE id = %s', (sub_id,))
            if cid:
                cursor.execute('DELETE FROM user_subscriptions WHERE chat_id = %s', (cid,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            raise Exception(f"Err: {e}")
        conn.close()


def is_user_subscribed_to_channel(user_id, chat_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ('member', 'administrator', 'creator')
    except Exception:
        return False


def check_required_subscriptions(user_id, chat_id, message_id=None, sender_chat=None):
    if sender_chat is not None:
        return True
    if user_id == OWNER_ID:
        return True
    bid = get_bot_id()
    if bid and user_id == bid:
        return True
    key = (user_id, chat_id)
    now = time.time()
    c = sub_check_cache.get(key)
    if c and c[0] > now:
        return c[1]
    try:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('SELECT sub_required FROM chats WHERE chat_id = %s', (chat_id,))
        row = cursor.fetchone()
        conn.close()
        if not row or row['sub_required'] == 0:
            sub_check_cache[key] = (now + SUB_CACHE_TTL, True)
            return True
    except Exception:
        return True
    subs = get_required_subscriptions()
    if not subs:
        sub_check_cache[key] = (now + SUB_CACHE_TTL, True)
        return True
    nc = []
    for sub in subs:
        if not is_user_subscribed_to_channel(user_id, sub['chat_id']):
            nc.append(sub)
    if nc:
        unsub_attempts[key] = unsub_attempts.get(key, 0) + 1
        att = unsub_attempts[key]
        if att >= 5:
            unsub_attempts.pop(key, None)
            sub_check_cache[key] = (now + 60, False)
            try:
                bot.ban_chat_member(chat_id, user_id)
                bot.unban_chat_member(chat_id, user_id)
                safe_send(chat_id, f"👢 {get_user_display_by_id(user_id)} кикнут!", parse_mode='HTML')
            except Exception:
                pass
            return False
        if message_id:
            try:
                bot.delete_message(chat_id, message_id)
            except Exception:
                pass
        user = get_or_create_user(user_id, "", "")
        text = f"⚠️ <b>{get_user_display(user)}</b>, нужно подписаться:\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for sub in nc:
            text += f"• <b>{sub['title']}</b>\n"
            link = sub['link']
            if not link.startswith('http'):
                link = f'https://t.me/{link[1:]}' if link.startswith('@') else f'https://t.me/{link}'
            markup.add(btn(f"📌 {sub['title']}", url=link, style='primary'))
        markup.add(btn("Я подписался", callback_data="check_subscribe", style='success'))
        text += f"\nОсталось: <b>{5 - att}</b>"
        safe_send(chat_id, text, parse_mode='HTML', reply_markup=markup)
        sub_check_cache[key] = (now + 5, False)
        return False
    else:
        unsub_attempts.pop(key, None)
        sub_check_cache[key] = (now + SUB_CACHE_TTL, True)
    return True


@bot.callback_query_handler(func=lambda call: call.data == "check_subscribe")
def handle_subscribe_check(call):
    try:
        uid = call.from_user.id
        cid = call.message.chat.id
        sub_check_cache.pop((uid, cid), None)
        if check_required_subscriptions(uid, cid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            safe_answer(call.id, "✅ Подтверждено!")
        else:
            safe_answer(call.id, "❌ Не все требования.", show_alert=True)
    except Exception:
        safe_answer(call.id, "❌ Ошибка!", show_alert=True)


# ---------- МЕНЮ ----------

def get_main_menu(user):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(btn("Профиль", callback_data="show_profile", style='success', icon=ICO_PROFILE),
               btn("Пополнить", callback_data="donate_menu", style='success', icon=ICO_DONATE))
    if user['bio_bonus_active'] == 1:
        rem = get_bio_bonus_remaining_seconds(user)
        markup.add(btn(f"VIP +{user.get('vip_amount', 5000)} через {format_bio_bonus_time(rem)}",
                       callback_data="bio_bonus_info", style='success', icon=ICO_VIP))
    else:
        markup.add(btn("Бесплатные 5000/7500 ноксов + VIP",
                       callback_data="bio_bonus_info", style='success', icon=ICO_VIP))
    markup.add(btn("Промокод", callback_data="enter_promo", style='primary', icon=ICO_PROMO),
               btn("Правила", callback_data="show_rules", style='primary', icon=ICO_RULES))
    markup.add(btn("Наш канал", url="https://t.me/NoxHubs", style='danger', icon=ICO_CHANNEL),
               btn("Чатик", url="https://t.me/Nox_chatik", style='danger', icon=ICO_CHAT))
    markup.add(btn("Поддержка", url=f"t.me/{OWNER_USERNAME}", style='danger', icon=ICO_SUPPORT))
    if is_co_owner(user['user_id']):
        markup.add(btn("Админ-панель", callback_data="admin_panel", style='danger', icon=ICO_ADMIN))
    return markup


def _vip_info_text(uid, username, first_name):
    user = get_or_create_user(uid, username or "", first_name or "")
    has = user['bio_bonus_active'] == 1
    vip_amt = user.get('vip_amount', 0) or 0
    has_bio, has_nick = check_vip_links(uid, username, first_name)

    text = (f"{EMO_VIP} <b>5000 / 7500 НОКСОВ + VIP-ЗНАЧОК</b> {EMO_VIP}\n\n"
            f"<b>Что даёт:</b>\n"
            f"• {EMO_NOX} <b>+5,000 ноксов</b> если ссылка только в <b>нико</b> или только в <b>Bio</b>\n"
            f"• {EMO_NOX} <b>+7,500 ноксов</b> если ссылка <b>и в нико, и в Bio</b>\n"
            f"• {EMO_NOX} <b>столько же каждый день</b> в 00:00 МСК\n"
            f"• {EMO_VIP} <b>VIP-значок</b> рядом с ником\n\n"
            f"<b>Куда вставить ссылку:</b>\n"
            f"1. В <b>ник</b> (имя) Telegram — например «Иван @Nox_chatik»\n"
            f"2. В поле «О себе» (Bio)\n\n"
            f"<b>Подходящие ссылки:</b>\n"
            f"• <code>@Nox_chatik</code>\n"
            f"• <code>@NoxHubBot</code>\n"
            f"• <code>https://t.me/Nox_chatik</code>\n\n"
            f"{EMO_BULB} Просто напиши любое сообщение в чате — бот сам найдёт ссылку и подключит VIP.\n\n"
            f"{EMO_CANCEL} Уберёшь ссылку — VIP снимется и спишется текущая сумма.\n\n")

    if has:
        rem = get_bio_bonus_remaining_seconds(user)
        text += (f"{EMO_VIP} <b>СТАТУС: VIP АКТИВЕН</b> ({vip_amt} в день)\n"
                 f"Следующий бонус через <b>{format_bio_bonus_time(rem)}</b>")
        alert = f"VIP активен ({vip_amt}) • +{vip_amt} через {format_bio_bonus_time(rem)}"
    elif has_bio or has_nick:
        amt = BIO_BONUS_AMOUNT_BOTH if (has_bio and has_nick) else BIO_BONUS_AMOUNT
        text += (f"{EMO_BULB} <b>Ссылка найдена!</b> Ты получишь <b>{amt:,}</b>.\n"
                 f"Напиши любое сообщение в @Nox_chatik — бот активирует VIP.")
        alert = f"✅ Ссылка найдена! Напиши в чат → +{amt}"
    else:
        text += (f"{EMO_CANCEL} <b>Статус: не подключено.</b>\n"
                 f"Добавь ссылку в ник или Bio и напиши в @Nox_chatik.")
        alert = "❌ Добавь ссылку и напиши в чат"

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(btn("Открыть чат", url=CHAT_LINK, style='danger', icon=ICO_CHAT))
    markup.add(btn("Назад", callback_data="back_to_menu", style='primary', icon=ICO_BACK))
    return text, markup, alert


@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for nu in message.new_chat_members:
        if nu.is_bot:
            if nu.id == get_bot_id():
                add_chat(message.chat.id, message.chat.title)
                safe_send(message.chat.id, f"{EMO_SAFE} Бот активирован!", parse_mode='HTML')
                try:
                    link = get_chat_link(message.chat.id)
                    title = message.chat.title or str(message.chat.id)
                    adder = message.from_user
                    ad = (adder.first_name or adder.username or f"id{adder.id}") if adder else "—"
                    notif = f"🆕 <b>Бот добавлен!</b>\n📛 <b>{title}</b>\n🆔 <code>{message.chat.id}</code>\n👤 {ad}"
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    if link:
                        notif += f"\n🔗 {link}"
                        markup.add(btn("Открыть", url=link, style='primary', icon=ICO_CHAT))
                    safe_send(OWNER_ID, notif, parse_mode='HTML', reply_markup=markup)
                except Exception:
                    pass
            continue
        user = get_or_create_user(nu.id, nu.username, nu.first_name)
        wt = (f"{EMO_WELCOME} <b>Добро пожаловать в NoxHub, {get_user_display(user)}!</b>\n\n"
              f"{EMO_BONUS} Стартовый баланс — 2000 {EMO_NOX}\n\n"
              f"<b>{EMO_RULES} ПРАВИЛА</b> — напишите <b>правила</b>\n"
              f"<b>{EMO_DICE} ИГРЫ</b> — команда <b>игры</b>\n\n"
              f"{EMO_PROFILE} <code>профиль</code> | {EMO_NOX} <code>б</code> | {EMO_TROPHY} <code>топ богатых</code>")
        safe_send(message.chat.id, wt, parse_mode='HTML')


@bot.message_handler(content_types=['left_chat_member'])
def handle_left_member(message):
    lu = message.left_chat_member
    if lu.is_bot:
        if lu.id == get_bot_id():
            try:
                with db_lock:
                    conn = get_db_connection()
                    cursor = db_cursor(conn)
                    cursor.execute('DELETE FROM chats WHERE chat_id = %s', (message.chat.id,))
                    conn.commit()
                    conn.close()
            except Exception:
                pass
        return
    ud = get_or_create_user(lu.id, lu.username, lu.first_name)
    safe_send(message.chat.id, f"{EMO_WELCOME} {get_user_display(ud)} вышел 🤦🏿‍♂️", parse_mode='HTML')


def donate_menu_start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(btn("За рубли", callback_data="donate_rubles", style='primary', icon=ICO_RUBLES))
    markup.add(btn("За звёзды", callback_data="donate_stars", style='success', icon=ICO_STARS))
    markup.add(btn("Назад", callback_data="back_to_menu", style='danger', icon=ICO_BACK))
    text = (f"{EMO_DONATE} <b>ПОПОЛНЕНИЕ</b>\n\n"
            f"{EMO_RUBLES} 1 ₽ = 400 {EMO_NOX} (мин 25000)\n"
            f"{EMO_STARS} 1 ⭐ = 400 {EMO_NOX} (мин 15)")
    try:
        bot.send_photo(message.chat.id, BOT_PHOTO_URL, caption=text, reply_markup=markup, parse_mode='HTML')
    except Exception:
        safe_send(message.chat.id, text, reply_markup=markup, parse_mode='HTML')


@bot.message_handler(commands=['start'])
def cmd_start(message):
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    args = message.text.split()
    if len(args) > 1 and args[1] == 'donate':
        donate_menu_start(message)
        return
    if len(args) > 1 and args[1] == 'vip':
        text, markup, _ = _vip_info_text(message.from_user.id, message.from_user.username, message.from_user.first_name)
        try:
            bot.send_photo(message.chat.id, BOT_PHOTO_URL, caption=text, reply_markup=markup, parse_mode='HTML')
        except Exception:
            safe_send(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
        return
    markup = get_main_menu(user)
    name = user['first_name'] or user['username'] or "Гость"
    text = f"{EMO_WELCOME} Добро пожаловать, {name}!\n\nВыбери раздел ниже {EMO_DOWN}"
    try:
        bot.send_photo(message.chat.id, BOT_PHOTO_URL, caption=text, reply_markup=markup, parse_mode='HTML')
    except Exception:
        safe_send(message.chat.id, text, reply_markup=markup, parse_mode='HTML')


@bot.message_handler(commands=['игры'])
@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'игры')
def cmd_list_games(message):
    safe_send(message.chat.id, build_games_list(), parse_mode='HTML')


def build_games_list():
    return (f"{EMO_DICE} <b>СПИСОК ИГР</b>\n\n"
            f"{EMO_PVP_HEADER} <b>ПВП</b>\n\n"
            f"{EMO_DICE} <code>кости [ставка]</code>\n{DIV_PVP_LINE}\n"
            f"{EMO_ROCK} <code>цуефа [ставка]</code>\n{DIV_PVP_LINE}\n"
            f"{EMO_TTT_INVITE} <code>крестики [ставка]</code>\n{DIV_PVP_LINE}\n"
            f"{EMO_MINE} <code>мины [ставка]</code>\n{DIV_PVP_LINE}\n"
            f"{EMO_NUMBER} <code>число [макс] [ставка]</code>\n{DIV_PVP_LINE}\n"
            f"{EMO_ROULETTE} <code>рулетка [ставка]</code>\n{DIV_PVP_LINE}\n"
            f"{EMO_EAGLE} <code>орел [ставка]</code>\n\n"
            f"{EMO_SOLO_HEADER} <b>СОЛО</b>\n\n"
            f"{EMO_SLOTS} <code>слот [ставка]</code>\n{DIV_SOLO_LINE}\n"
            f"{EMO_CHEST} <code>сундук [ставка]</code>\n{DIV_SOLO_LINE}\n"
            f"{EMO_FLOOR} <code>этажи [ставка]</code>\n\n"
            f"{EMO_BULB} <i>вместо ставки <b>вб</b></i>")


# ---------- ИНСТРУКЦИЯ VIP ----------

@bot.callback_query_handler(func=lambda call: call.data == "bio_bonus_info")
def bio_bonus_info_cb(call):
    try:
        uid = call.from_user.id
        cid = call.message.chat.id
        text, markup, alert = _vip_info_text(uid, call.from_user.username, call.from_user.first_name)
        safe_answer(call.id, alert, show_alert=True)
        try:
            safe_edit(cid, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
        except Exception:
            safe_send(cid, text, reply_markup=markup, parse_mode='HTML')
    except Exception as e:
        print(f"[BIO INFO ERR] {e}")
        safe_answer(call.id, "❌ Ошибка", show_alert=True)


# ---------- КОМАНДА "б" ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'б')
def cmd_balance_short(message):
    try:
        if check_banned(message.from_user.id, message.chat.id):
            return
        if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id,
                                            sender_chat=message.sender_chat):
            return
        bu = bot.get_me().username
        user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        today = get_moscow_date()
        dt = user['last_bonus_date'] == today
        qr = get_quick_bonus_remaining(user)
        if not dt:
            bl, bi = "Бонус", ICO_BONUS_ICO
        elif qr == 0:
            bl, bi = f"+{QUICK_BONUS_AMOUNT}", ICO_GOLD_BTN
        else:
            bl, bi = f"Бонус {format_time(qr)}", ICO_BONUS_ICO
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Пополнить", url=f"https://t.me/{bu}?start=donate", style='success', icon=ICO_DONATE),
                   btn(bl, callback_data=f"quick_bonus_{user['user_id']}", style='primary', icon=bi))
        if message.reply_to_message:
            tid = message.reply_to_message.from_user.id
            tu = get_or_create_user(tid, message.reply_to_message.from_user.username,
                                    message.reply_to_message.from_user.first_name)
            safe_send(message.chat.id, build_balance_text(tu), parse_mode='HTML', reply_markup=markup)
            return
        safe_send(message.chat.id, build_balance_text(user), parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"[BALANCE ERR] {e}")


def build_bonus_state(user):
    if user['last_bonus_date'] != get_moscow_date():
        return 0
    return 1 if get_quick_bonus_remaining(user) == 0 else 2


def build_balance_keyboard(user):
    bu = bot.get_me().username
    today = get_moscow_date()
    dt = user['last_bonus_date'] == today
    qr = get_quick_bonus_remaining(user)
    if not dt:
        bl, bi = "Бонус", ICO_BONUS_ICO
    elif qr == 0:
        bl, bi = f"+{QUICK_BONUS_AMOUNT}", ICO_GOLD_BTN
    else:
        bl, bi = f"Бонус {format_time(qr)}", ICO_BONUS_ICO
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(btn("Пополнить", url=f"https://t.me/{bu}?start=donate", style='success', icon=ICO_DONATE),
               btn(bl, callback_data=f"quick_bonus_{user['user_id']}", style='primary', icon=bi))
    return markup


@bot.callback_query_handler(func=lambda call: call.data.startswith("quick_bonus"))
def quick_bonus_handler(call):
    try:
        if call.data == "quick_bonus":
            uid = call.from_user.id
        else:
            parts = call.data.split("_", 2)
            uid = int(parts[2]) if len(parts) >= 3 else call.from_user.id
            if call.from_user.id != uid:
                safe_answer(call.id, "🖕 Не твоя!", show_alert=True)
                return
        user = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
        st = build_bonus_state(user)
        if st == 0:
            bonus = random.randint(850, 1200)
            jp = random.random() * 10000 < 1
            if jp:
                bonus = 50000
            with db_lock:
                conn = get_db_connection()
                cursor = db_cursor(conn)
                cursor.execute('UPDATE users SET balance = balance + %s, last_bonus_date = %s WHERE user_id = %s',
                               (bonus, get_moscow_date(), uid))
                conn.commit()
                conn.close()
            safe_answer(call.id, f"🎉 ДЖЕКПОТ! +{bonus:,}!" if jp else f"🎁 +{bonus:,}!", show_alert=True)
        elif st == 1:
            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat()
            with db_lock:
                conn = get_db_connection()
                cursor = db_cursor(conn)
                cursor.execute('UPDATE users SET balance = balance + %s, last_quick_bonus = %s WHERE user_id = %s',
                               (QUICK_BONUS_AMOUNT, now, uid))
                conn.commit()
                conn.close()
            safe_answer(call.id, f"💰 +{QUICK_BONUS_AMOUNT}!", show_alert=True)
        else:
            safe_answer(call.id, f"⏱ Через {format_time(get_quick_bonus_remaining(user))}", show_alert=True)
        upd = get_or_create_user(uid, "", "")
        try:
            safe_edit(call.message.chat.id, call.message.message_id, build_balance_text(upd),
                      reply_markup=build_balance_keyboard(upd), parse_mode='HTML')
        except Exception:
            pass
    except Exception:
        safe_answer(call.id, "❌ Ошибка", show_alert=True)


# ---------- ПЕРЕВОДЫ ----------

@bot.message_handler(func=lambda m: m.text and re.match(r'^п\s+\d+\s+@?\w+$', m.text.strip().lower()))
def cmd_transfer_by_username(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id,
                                        sender_chat=message.sender_chat):
        return
    parts = message.text.strip().split()
    if len(parts) < 3:
        safe_send(message.chat.id, f"{EMO_CANCEL} Формат: <code>п [сумма] @user</code>", parse_mode='HTML')
        return
    amount = int(parts[1])
    target_str = parts[2]
    if amount <= 0:
        safe_send(message.chat.id, f"{EMO_CANCEL} Сумма > 0!", parse_mode='HTML')
        return
    tid = None
    try:
        if target_str.startswith('@'):
            tid = bot.get_chat_member(message.chat.id, target_str).user.id
        else:
            try:
                tid = int(target_str)
            except ValueError:
                tid = bot.get_chat_member(message.chat.id, f"@{target_str}").user.id
    except Exception:
        safe_send(message.chat.id, f"{EMO_CANCEL} Не найден.", parse_mode='HTML')
        return
    if tid == message.from_user.id:
        safe_send(message.chat.id, f"{EMO_CANCEL} Себе нельзя!", parse_mode='HTML')
        return
    fu = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    tu = get_or_create_user(tid, "", "")
    if fu['balance'] < amount:
        safe_send(message.chat.id, f"{EMO_CANCEL} Мало! Нужно {amount:,}, у тебя {fu['balance']:,}", parse_mode='HTML')
        return
    update_balance(fu['user_id'], -amount)
    update_balance(tu['user_id'], amount)
    safe_send(message.chat.id, f"{get_user_display(fu)} → {amount:,} {EMO_NOX} → {get_user_display(tu)}!", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and re.match(r'^п\s+\d+$', m.text.strip().lower()))
def cmd_transfer_short(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id,
                                        sender_chat=message.sender_chat):
        return
    if not message.reply_to_message:
        safe_send(message.chat.id, f"{EMO_CANCEL} Ответь на сообщение.", parse_mode='HTML')
        return
    match = re.match(r'^п\s+(\d+)$', message.text.strip().lower())
    if not match:
        return
    amount = int(match.group(1))
    if amount <= 0:
        return
    fu = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    tu = get_or_create_user(message.reply_to_message.from_user.id, message.reply_to_message.from_user.username,
                            message.reply_to_message.from_user.first_name)
    if fu['user_id'] == tu['user_id']:
        safe_send(message.chat.id, f"{EMO_CANCEL} Себе нельзя!", parse_mode='HTML')
        return
    if fu['balance'] < amount:
        safe_send(message.chat.id, f"{EMO_CANCEL} Мало!", parse_mode='HTML')
        return
    update_balance(fu['user_id'], -amount)
    update_balance(tu['user_id'], amount)
    safe_send(message.chat.id, f"{get_user_display(fu)} → {amount:,} {EMO_NOX} → {get_user_display(tu)}!", parse_mode='HTML')


# ---------- ПРОФИЛЬ / ПРАВИЛА / БОНУС / ТОП ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'профиль')
def cmd_profile(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id,
                                        sender_chat=message.sender_chat):
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    stats = get_all_stats(user['user_id'])
    tw = sum(d['wins'] for d in stats.values())
    tl = sum(d['losses'] for d in stats.values())
    tg = tw + tl
    tr = 0.0 if tg == 0 else round((tw / tg) * 100, 1)
    text = (f"{EMO_PROFILE} <b>ПРОФИЛЬ:</b> {get_user_display(user)}\n"
            f"{EMO_NOX} <b>Баланс:</b> <code>{user['balance']:,}</code>\n"
            f"{EMO_FIRE} <b>Серия:</b> <code>{user['current_streak']}</code>\n"
            f"{EMO_TROPHY} <b>Рекорд:</b> <code>{user['max_streak']}</code>\n\n"
            f"📊 <b>ОБЩАЯ:</b> 🟢 {tw} | 🔴 {tl} | {EMO_MULT} {tr}%\n")
    for gt, d in stats.items():
        text += f"\n<b>{d['name']}</b>\n   🟢 {d['wins']} | 🔴 {d['losses']} | {EMO_MULT} {d['winrate']}%\n"
    safe_send(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'тп')
def cmd_other_profile(message):
    if not message.reply_to_message:
        safe_send(message.chat.id, f"{EMO_CANCEL} Ответь на сообщение!", parse_mode='HTML')
        return
    tid = message.reply_to_message.from_user.id
    tu = get_or_create_user(tid, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
    stats = get_all_stats(tid)
    tw = sum(d['wins'] for d in stats.values())
    tl = sum(d['losses'] for d in stats.values())
    tg = tw + tl
    tr = 0.0 if tg == 0 else round((tw / tg) * 100, 1)
    text = (f"{EMO_PROFILE} <b>ПРОФИЛЬ:</b> {get_user_display(tu)}\n"
            f"{EMO_NOX} <b>Баланс:</b> <code>{tu['balance']:,}</code>\n"
            f"{EMO_FIRE} <b>Серия:</b> <code>{tu['current_streak']}</code>\n"
            f"{EMO_TROPHY} <b>Рекорд:</b> <code>{tu['max_streak']}</code>\n\n"
            f"📊 <b>ОБЩАЯ:</b> 🟢 {tw} | 🔴 {tl} | {EMO_MULT} {tr}%\n")
    safe_send(message.chat.id, text, parse_mode='HTML')


RULES_TEXT = (f"{EMO_RULES} <b>ПРАВИЛА NOXHUB</b>\n\n"
              f"<i>Обязательны для всех.</i>\n\n"
              f"{EMO_CANCEL} <b>ЗАПРЕЩЕНО</b>\n"
              f"• 18+ — мут 2ч\n"
              f"• Расчлененка — мут 2ч\n"
              f"• Спам — мут 2ч\n"
              f"• Реклама — мут 10ч\n\n"
              f"{EMO_REPORT} <b>ЖАЛОБЫ</b> — модераторам.\n\n"
              f"{EMO_BULB} Все игры: <b>игры</b>")


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'правила')
def cmd_rules(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id,
                                        sender_chat=message.sender_chat):
        return
    safe_send(message.chat.id, RULES_TEXT, parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'бонус')
def cmd_bonus(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    dt = user['last_bonus_date'] == get_moscow_date()
    qr = get_quick_bonus_remaining(user)
    if not dt:
        bl, bi = "Забрать ежедневный бонус", ICO_BONUS_ICO
    elif qr == 0:
        bl, bi = f"Забрать +{QUICK_BONUS_AMOUNT}", ICO_GOLD_BTN
    else:
        bl, bi = f"Бонус {format_time(qr)}", ICO_BONUS_ICO
    markup = types.InlineKeyboardMarkup()
    markup.add(btn(bl, callback_data=f"quick_bonus_{user['user_id']}", style='success', icon=bi))
    text = (f"{EMO_BONUS} <b>БОНУСЫ</b>\n\n1️⃣ Ежедневный — 850-1200 {EMO_NOX}\n"
            f"2️⃣ Каждые 10 мин — +{QUICK_BONUS_AMOUNT} {EMO_NOX}\n"
            f"3️⃣ <b>5000/7500 сразу + VIP-значок {EMO_VIP}</b> — в главном меню\n\n{EMO_BULB} Жми кнопку!")
    safe_send(message.chat.id, text, reply_markup=markup, parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'топ богатых')
def cmd_top(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('SELECT user_id, username, first_name, balance, bio_bonus_active, vip_amount FROM users ORDER BY balance DESC LIMIT 10')
        rows = cursor.fetchall()
        conn.close()
    if not rows:
        safe_send(message.chat.id, f"{EMO_CANCEL} Нет.", parse_mode='HTML')
        return
    text = f"{EMO_TROPHY} <b>ТОП-10</b>\n\n"
    for i, row in enumerate(rows, 1):
        u = dict(row)
        text += f"{i}. {get_user_display(u)}\n   {EMO_NOX}: <code>{u['balance']:,}</code>\n"
    safe_send(message.chat.id, text, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "show_rules")
def show_rules(call):
    text = (f"{EMO_RULES} <b>ПРАВИЛА NOXHUB</b>\n\n{EMO_BULB} Все игры: <b>игры</b>\n\n"
            f"<b>{EMO_BONUS} БОНУСЫ</b>\n   <code>бонус</code>\n\n"
            f"<b>⚡ КОМАНДЫ</b>\n   {EMO_PROFILE} <code>профиль</code>\n   {EMO_NOX} <code>б</code>\n   {EMO_TROPHY} <code>топ богатых</code>\n\n"
            f"💬 @Nox_chatik | {EMO_CHANNEL} @NoxHubs")
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("Назад", callback_data="back_to_menu", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "show_profile")
def show_profile(call):
    uid = call.from_user.id
    user = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
    stats = get_all_stats(uid)
    tw = sum(d['wins'] for d in stats.values())
    tl = sum(d['losses'] for d in stats.values())
    tg = tw + tl
    tr = 0.0 if tg == 0 else round((tw / tg) * 100, 1)
    text = (f"{EMO_PROFILE} <b>ПРОФИЛЬ:</b> {get_user_display(user)}\n"
            f"{EMO_NOX} <b>Баланс:</b> <code>{user['balance']:,}</code>\n"
            f"{EMO_FIRE} <b>Серия:</b> <code>{user['current_streak']}</code>\n"
            f"{EMO_TROPHY} <b>Рекорд:</b> <code>{user['max_streak']}</code>\n\n"
            f"📊 <b>ОБЩАЯ:</b> 🟢 {tw} | 🔴 {tl} | {EMO_MULT} {tr}%\n")
    for gt, d in stats.items():
        text += f"\n<b>{d['name']}</b>\n   🟢 {d['wins']} | 🔴 {d['losses']} | {EMO_MULT} {d['winrate']}%\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("Назад", callback_data="back_to_menu", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    user = get_or_create_user(call.from_user.id, call.from_user.username, call.from_user.first_name)
    markup = get_main_menu(user)
    safe_edit(call.message.chat.id, call.message.message_id, f"✨ NoxHub\n\nВыбери раздел {EMO_DOWN}",
              reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


# ---------- ПРОМОКОД ----------

@bot.callback_query_handler(func=lambda call: call.data == "enter_promo")
def enter_promo(call):
    msg = safe_send(call.message.chat.id, f"{EMO_PROMO} Введи промокод:", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_promo_redeem)
    safe_answer(call.id)


def process_promo_redeem(message):
    code = message.text.strip()
    uid = message.from_user.id
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('SELECT * FROM promos WHERE code = %s', (code,))
        promo = cursor.fetchone()
        if not promo:
            safe_send(message.chat.id, f"{EMO_CANCEL} Не найден.", parse_mode='HTML')
            conn.close()
            return
        cursor.execute('SELECT * FROM promo_history WHERE code = %s AND user_id = %s', (code, uid))
        if cursor.fetchone():
            safe_send(message.chat.id, f"{EMO_CANCEL} Уже активирован!", parse_mode='HTML')
            conn.close()
            return
        if promo['current_uses'] >= promo['max_uses']:
            safe_send(message.chat.id, f"{EMO_CANCEL} Лимит.", parse_mode='HTML')
            conn.close()
            return
        cursor.execute('UPDATE promos SET current_uses = current_uses + 1 WHERE code = %s', (code,))
        cursor.execute('INSERT INTO promo_history (code, user_id) VALUES (%s, %s)', (code, uid))
        conn.commit()
        conn.close()
    update_balance(uid, promo['reward'])
    safe_send(message.chat.id, f"{EMO_PROMO} +{promo['reward']:,} {EMO_NOX}", parse_mode='HTML')


# ---------- ДОНАТ ----------

@bot.callback_query_handler(func=lambda call: call.data == "donate_menu")
def donate_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(btn("За рубли", callback_data="donate_rubles", style='primary', icon=ICO_RUBLES))
    markup.add(btn("За звёзды", callback_data="donate_stars", style='success', icon=ICO_STARS))
    markup.add(btn("Назад", callback_data="back_to_menu", style='danger', icon=ICO_BACK))
    text = (f"{EMO_DONATE} <b>ПОПОЛНЕНИЕ</b>\n\n{EMO_RUBLES} 1 ₽ = 400 {EMO_NOX} (мин 25000)\n"
            f"{EMO_STARS} 1 ⭐ = 400 {EMO_NOX} (мин 15)")
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "donate_rubles")
def donate_rubles(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("Ввести сумму", callback_data="donate_input", style='primary', icon=ICO_INPUT))
    markup.add(btn("Назад", callback_data="donate_menu", style='danger', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id,
              f"{EMO_RUBLES} <b>ЗА РУБЛИ</b>\n\n1 ₽ = 400 {EMO_NOX}\nМинимум: <b>25 000</b>",
              reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "donate_input")
def donate_input(call):
    msg = safe_send(call.message.chat.id, f"{EMO_INPUT} Кол-во (мин 25000):", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_donate_amount)
    safe_answer(call.id)


def process_donate_amount(message):
    uid = message.from_user.id
    try:
        nox = int(message.text.strip())
        if nox < 25000:
            safe_send(message.chat.id, f"{EMO_CANCEL} Минимум 25 000!", parse_mode='HTML')
            return
        rub = round(nox / 400, 2)
        temp_donate[uid] = {'nox': nox, 'rub': rub, 'type': 'rubles'}
        markup = types.InlineKeyboardMarkup()
        markup.add(btn("Оплатить", callback_data="donate_pay", style='success', icon=ICO_DONATE))
        markup.add(btn("Отмена", callback_data="donate_cancel", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"💳 {nox:,} {EMO_NOX} за <b>{rub} ₽</b>?", reply_markup=markup, parse_mode='HTML')
    except ValueError:
        safe_send(message.chat.id, f"{EMO_CANCEL} Число!", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "donate_pay")
def donate_pay(call):
    uid = call.from_user.id
    if uid not in temp_donate:
        safe_answer(call.id, "❌ Устарело.", show_alert=True)
        return
    data = temp_donate.pop(uid)
    nox, rub = data['nox'], data['rub']
    text = (f"💳 <b>{nox:,} {EMO_NOX}</b>\n\n💰 <b>{rub} ₽</b>\n🏦 Карта: <code>{CARD_NUMBER}</code>\n\n1️⃣ Переведи\n2️⃣ Скрин\n3️⃣ Жми кнопку")
    owner_text = f"💳 Оплатил {nox:,} ноксов ({rub} ₽)."
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("Я оплатил", url=f"tg://resolve?domain={OWNER_USERNAME}&text={owner_text}", style='success', icon=ICO_DONATE))
    markup.add(btn("Назад", callback_data="donate_rubles", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "donate_stars")
def donate_stars(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("Ввести звёзды", callback_data="donate_stars_input", style='primary', icon=ICO_INPUT))
    markup.add(btn("Назад", callback_data="donate_menu", style='danger', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id,
              f"{EMO_STARS} <b>ЗА ЗВЁЗДЫ</b>\n\n1 ⭐ = 400 {EMO_NOX}\nМинимум: <b>15 ⭐</b>",
              reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "donate_stars_input")
def donate_stars_input(call):
    msg = safe_send(call.message.chat.id, f"{EMO_INPUT} Кол-во звёзд:", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_donate_stars_amount)
    safe_answer(call.id)


def process_donate_stars_amount(message):
    uid = message.from_user.id
    try:
        stars = int(message.text.strip())
        if stars < 15:
            safe_send(message.chat.id, f"{EMO_CANCEL} Минимум 15 ⭐!", parse_mode='HTML')
            return
        nox = stars * 400
        temp_donate[uid] = {'stars': stars, 'nox': nox, 'type': 'stars'}
        markup = types.InlineKeyboardMarkup()
        markup.add(btn("Оплатить", callback_data="donate_stars_pay", style='success', icon=ICO_DONATE))
        markup.add(btn("Отмена", callback_data="donate_cancel", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_STARS} {nox:,} {EMO_NOX} за {stars} ⭐", reply_markup=markup, parse_mode='HTML')
    except ValueError:
        safe_send(message.chat.id, f"{EMO_CANCEL} Число!", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "donate_stars_pay")
def donate_stars_pay(call):
    uid = call.from_user.id
    if uid not in temp_donate:
        safe_answer(call.id, "❌", show_alert=True)
        return
    data = temp_donate.pop(uid)
    stars, nox = data['stars'], data['nox']
    text = f"{EMO_STARS} {nox:,} {EMO_NOX} за <b>{stars} ⭐</b>"
    owner_text = f"⭐ Оплатил {stars} звёзд."
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("Владельцу", url=f"tg://resolve?domain={OWNER_USERNAME}&text={owner_text}", style='success', icon=ICO_SUPPORT))
    markup.add(btn("Назад", callback_data="donate_stars", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "donate_cancel")
def donate_cancel(call):
    temp_donate.pop(call.from_user.id, None)
    safe_edit(call.message.chat.id, call.message.message_id, f"{EMO_CANCEL} Отменено.", parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "show_games")
def show_games_callback(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("Назад", callback_data="back_to_menu", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, build_games_list(), reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


# ================== ИГРЫ ==================
user_decks = {}


def is_player_in_active_game(uid):
    for cg in list(active_games.values()):
        for g in list(cg.values()):
            if g.get('p1_id') == uid or g.get('p2_id') == uid:
                return True
            if g.get('current_turn') == uid:
                return True
            if g.get('chooser_id') == uid or g.get('guesser_id') == uid:
                return True
    return False


def check_player_in_game(uid):
    if uid not in player_in_game:
        return False
    if not is_player_in_active_game(uid):
        player_in_game.discard(uid)
        return False
    return True


def add_player_to_game(uid):
    player_in_game.add(uid)


def remove_player_from_game(uid):
    player_in_game.discard(uid)


def force_cleanup_player(uid):
    for cid, cg in list(active_games.items()):
        for gid, g in list(cg.items()):
            if g.get('p1_id') == uid or g.get('p2_id') == uid or g.get('current_turn') == uid \
                    or g.get('chooser_id') == uid or g.get('guesser_id') == uid:
                del active_games[cid][gid]
        if cid in active_games and not active_games[cid]:
            del active_games[cid]
    player_in_game.discard(uid)


def finalize_game(chat_id, wid, lid, stake, gt, result, msg_id=None):
    if result == 'win':
        wa = stake * 2
        update_balance(wid, wa)
        update_streak(wid, True, stake)
        update_streak(lid, False, stake)
        update_game_stats(wid, gt, True)
        update_game_stats(lid, gt, False)
        safe_send(chat_id, f"{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - stake:,} {EMO_NOX}", parse_mode='HTML')
    elif result == 'draw':
        update_balance(wid, stake)
        update_balance(lid, stake)
        safe_send(chat_id, f"{EMO_HANDSHAKE} Ничья!")
    elif result == 'error':
        update_balance(wid, stake)
        update_balance(lid, stake)
        safe_send(chat_id, f"{EMO_CANCEL} Ошибка!", parse_mode='HTML')
    else:
        return
    remove_player_from_game(wid)
    remove_player_from_game(lid)
    if chat_id in active_games and msg_id in active_games[chat_id]:
        del active_games[chat_id][msg_id]
        if not active_games[chat_id]:
            del active_games[chat_id]


@bot.callback_query_handler(func=lambda call: call.data == "reset_solo_games")
def reset_solo_games(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    refund = 0
    if uid in solo_game_stakes:
        refund = solo_game_stakes.pop(uid)
        try:
            update_balance(uid, refund)
        except Exception:
            pass
    casino_in_progress[uid] = False
    chest_cache.pop(uid, None)
    if refund > 0:
        safe_answer(call.id, f"✅ Возврат {refund:,}!", show_alert=True)
        try:
            safe_edit(cid, call.message.message_id, f"{EMO_SAFE} Сброшено. Возврат: <code>{refund:,}</code>", parse_mode='HTML')
        except Exception:
            pass
    else:
        safe_answer(call.id, "✅ Сброшено!", show_alert=True)


# ---------- СЛОТЫ ----------

def _show_slots_row(sl):
    return ' | '.join(sl)


def _roll_and_show_free_spin(user_id, stake, index, total):
    outcome = roll_slot_outcome(0)
    pool = list(SLOT_SYMBOLS.values())
    random.shuffle(pool)
    syms = [emo_tag(eid, fb) for eid, fb in pool[:4]]
    row = f"[ {_show_slots_row(syms)} ]"
    if outcome in ('lose', 'bad_lose'):
        return f"#{index}/{total} {row}\nПроигрыш (фри)", 0
    if outcome == 'fifty':
        win = int(stake * 0.5)
        update_balance(user_id, win)
        return f"#{index}/{total} {row}\nВозврат 50% → +{win:,} {EMO_NOX} (фри)", win
    if outcome == 'devstv':
        return f"#{index}/{total} {row}\nТы умрёшь девственником (фри)", 0
    if outcome == 'minus2500':
        return f"#{index}/{total} {row}\nПустой спин (фри)", 0
    if outcome == 'neutral':
        return f"#{index}/{total} {row}\nЗачем ты родился (фри)", 0
    if outcome == 'clover':
        update_balance(user_id, 1000)
        return f"#{index}/{total} {row}\n+1,000 {EMO_NOX} (фри)", 1000
    if outcome == 'free10':
        return f"#{index}/{total} {row}\nПустой спин (фри)", 0
    if outcome in SLOT_MULT and outcome in SLOT_SYMBOLS:
        mult = SLOT_MULT[outcome]
        win = int(stake * mult)
        update_balance(user_id, win)
        if outcome == 'super_jackpot':
            return f"#{index}/{total} {row}\nSUPER JACKPOT x100 → +{win:,} {EMO_NOX} (фри)", win
        if outcome == 'diamond':
            return f"#{index}/{total} {row}\nx10 → +{win:,} {EMO_NOX} (фри)", win
        return f"#{index}/{total} {row}\nx{mult} → +{win:,} {EMO_NOX} (фри)", win
    return f"#{index}/{total} {row}\nОшибка", 0


def _run_free_spins(chat_id, user_id, stake):
    try:
        send_slot_result(chat_id, f"{EMO_BONUS} <b>10 ФРИ СПИНОВ</b> на {stake:,} {EMO_NOX} (без списания)")
    except Exception:
        pass
    total_win = 0
    for i in range(1, FREE_SPINS_COUNT + 1):
        try:
            text, gain = _roll_and_show_free_spin(user_id, stake, i, FREE_SPINS_COUNT)
            total_win += gain
            send_slot_result(chat_id, text)
        except Exception as e:
            print(f"[FREE SPIN ERR] {e}")
        time.sleep(FREE_SPIN_INTERVAL)
    user_final = get_or_create_user(user_id, "", "")
    send_slot_result(chat_id,
                     f"{EMO_TROPHY} <b>Фри спины готовы!</b>\n"
                     f"{EMO_NOX} Итого: <b>+{total_win:,}</b>\n"
                     f"{EMO_NOX} Баланс: <code>{user_final['balance']:,}</code>")


def _slots_send_result(chat_id, outcome, stake):
    try:
        if outcome in ('lose', 'bad_lose'):
            pool = list(SLOT_SYMBOLS.values())
            random.shuffle(pool)
            syms = [emo_tag(eid, fb) for eid, fb in pool[:4]]
            text = f"[ {_show_slots_row(syms)} ]\nПроигрыш. -{stake:,} {EMO_NOX}"
            send_slot_result(chat_id, text)
            return
        if outcome == 'fifty':
            eid, fb = SLOT_SYMBOLS['fifty']
            syms = [emo_tag(eid, fb)] * 4
            win = int(stake * 0.5)
            text = f"[ {_show_slots_row(syms)} ]\nВозврат 50% → +{win:,} {EMO_NOX}"
            send_slot_result(chat_id, text)
            return
        if outcome == 'devstv':
            eid, fb = SLOT_SYMBOLS['devstv']
            syms = [emo_tag(eid, fb)] * 4
            text = f"[ {_show_slots_row(syms)} ]\nТы умрёшь девственником"
            send_slot_result(chat_id, text)
            return
        if outcome == 'minus2500':
            eid, fb = SLOT_SYMBOLS['minus2500']
            syms = [emo_tag(eid, fb)] * 4
            text = f"[ {_show_slots_row(syms)} ]\n-{stake + 2500:,} {EMO_NOX}\nа чтоб жизнь малиной не казалась"
            send_slot_result(chat_id, text)
            return
        if outcome == 'neutral':
            eid, fb = SLOT_SYMBOLS['neutral']
            syms = [emo_tag(eid, fb)] * 4
            text = f"[ {_show_slots_row(syms)} ]\nЗачем ты вообще родился"
            send_slot_result(chat_id, text)
            return
        if outcome == 'free10':
            eid, fb = SLOT_SYMBOLS['free10']
            syms = [emo_tag(eid, fb)] * 4
            text = f"[ {_show_slots_row(syms)} ]\n10 ФРИ СПИНОВ! Ставка возвращена"
            send_slot_result(chat_id, text)
            return
        if outcome in SLOT_MULT and outcome in SLOT_SYMBOLS:
            eid, fb = SLOT_SYMBOLS[outcome]
            syms = [emo_tag(eid, fb)] * 4
            mult = SLOT_MULT[outcome]
            win = int(stake * mult)
            if outcome == 'super_jackpot':
                text = f"[ {_show_slots_row(syms)} ]\nSUPER JACKPOT x100 → +{win:,} {EMO_NOX}"
            elif outcome == 'diamond':
                text = f"[ {_show_slots_row(syms)} ]\nx10 → +{win:,} {EMO_NOX}"
            elif outcome == 'seven':
                text = f"[ {_show_slots_row(syms)} ]\nx3 → +{win:,} {EMO_NOX}"
            elif outcome == 'strawberry':
                text = f"[ {_show_slots_row(syms)} ]\nx2.5 → +{win:,} {EMO_NOX}"
            elif outcome == 'cherry':
                text = f"[ {_show_slots_row(syms)} ]\nx2 → +{win:,} {EMO_NOX}"
            elif outcome == 'kiwi':
                text = f"[ {_show_slots_row(syms)} ]\nx1.5 → +{win:,} {EMO_NOX}"
            elif outcome == 'new_1_2':
                text = f"[ {_show_slots_row(syms)} ]\nx1.2 → +{win:,} {EMO_NOX}"
            elif outcome == 'new_5':
                text = f"[ {_show_slots_row(syms)} ]\nx5 → +{win:,} {EMO_NOX}"
            else:
                text = f"[ {_show_slots_row(syms)} ]\nx{mult} → +{win:,} {EMO_NOX}"
            send_slot_result(chat_id, text)
            return
        send_slot_result(chat_id, f"Результат: {outcome}")
    except Exception as e:
        print(f"[SLOT SEND ERR] {e}")


def _do_slot_spin(uid, cid, user, stake):
    update_balance(uid, -stake)
    bal = user['balance'] - stake
    try:
        chain = 0
        while True:
            outcome = roll_slot_outcome(bal)
            if outcome in ('lose', 'bad_lose'):
                _slots_send_result(cid, 'lose', stake)
                break
            if outcome == 'fifty':
                win = int(stake * 0.5)
                update_balance(uid, win)
                _slots_send_result(cid, 'fifty', stake)
                break
            if outcome == 'devstv':
                _slots_send_result(cid, 'devstv', stake)
                break
            if outcome == 'minus2500':
                update_balance(uid, -2500)
                _slots_send_result(cid, 'minus2500', stake)
                break
            if outcome == 'neutral':
                _slots_send_result(cid, 'neutral', stake)
                break
            if outcome == 'clover':
                update_balance(uid, 1000)
                bal += 1000
                eid, fb = SLOT_SYMBOLS['clover']
                syms = [emo_tag(eid, fb)] * 4
                send_slot_result(cid, f"[ {_show_slots_row(syms)} ]\nФРИ СПИН! +1,000 {EMO_NOX}\n🔄 Крутим ещё...")
                chain += 1
                if chain >= 5:
                    send_slot_result(cid, "Цепочка из 5 фри спинов прервана.")
                    break
                continue
            if outcome == 'free10':
                update_balance(uid, stake)
                _slots_send_result(cid, 'free10', stake)
                threading.Thread(target=_run_free_spins, args=(cid, uid, stake), daemon=True).start()
                break
            if outcome in SLOT_MULT:
                mult = SLOT_MULT[outcome]
                win = int(stake * mult)
                update_balance(uid, win)
                _slots_send_result(cid, outcome, stake)
                break
            update_balance(uid, stake)
            send_slot_result(cid, f"⚠️ Неизвестный исход: {outcome}. Ставка возвращена.")
            break
    except Exception as e:
        print(f"[SLOTS ERR] {e}")
        try:
            update_balance(uid, stake)
            send_slot_result(cid, f"{EMO_CANCEL} Ошибка, ставка возвращена.")
        except Exception:
            pass


@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('слот'))
def cmd_slots_chat(message):
    if check_pm_game(message):
        return
    uid = message.from_user.id
    cid = message.chat.id
    if casino_in_progress.get(uid, False):
        markup = types.InlineKeyboardMarkup()
        markup.add(btn("Сбросить", callback_data="reset_solo_games", style='primary'))
        safe_send(cid, f"{EMO_TIMER} Уже есть игра!", reply_markup=markup, parse_mode='HTML')
        return
    match = re.match(r'^слот\s+(\S+)$', message.text.strip().lower())
    if not match:
        safe_send(cid, f"{EMO_BULB} <code>слот [ставка]</code>", parse_mode='HTML')
        return

    user = get_or_create_user(uid, message.from_user.username, message.from_user.first_name)
    sa = match.group(1).strip()
    if sa == 'вб':
        stake = user['balance']
    else:
        try:
            stake = int(sa)
        except ValueError:
            safe_send(cid, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
    if stake < 1:
        safe_send(cid, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
        return
    if user['balance'] < stake:
        safe_send(cid, f"{EMO_BULB} Мало!", parse_mode='HTML')
        return

    # Тихий кулдаун — ждём и крутим автоматически, без сообщения
    lock = get_slot_lock(uid)
    with lock:
        wait = SLOT_COOLDOWN_SECONDS - (time.time() - slot_cooldowns.get(uid, 0))
        if wait > 0:
            time.sleep(wait)
        slot_cooldowns[uid] = time.time()
        _do_slot_spin(uid, cid, user, stake)


# ---------- СУНДУК ----------

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('сундук'))
def cmd_chest(message):
    if check_pm_game(message):
        return
    uid = message.from_user.id
    cid = message.chat.id
    if casino_in_progress.get(uid, False):
        markup = types.InlineKeyboardMarkup()
        markup.add(btn("Сбросить", callback_data="reset_solo_games", style='primary'))
        safe_send(cid, f"{EMO_TIMER} Уже есть игра!", reply_markup=markup, parse_mode='HTML')
        return
    match = re.match(r'^сундук\s+(\S+)$', message.text.strip().lower())
    if not match:
        safe_send(cid, f"{EMO_BULB} <code>сундук [ставка]</code>", parse_mode="HTML")
        return
    user = get_or_create_user(uid, message.from_user.username, message.from_user.first_name)
    sa = match.group(1).strip()
    if sa == 'вб':
        stake = user['balance']
    else:
        try:
            stake = int(sa)
        except ValueError:
            safe_send(cid, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
    if stake < 1:
        safe_send(cid, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
        return
    if user['balance'] < stake:
        safe_send(cid, f"{EMO_BULB} Мало!", parse_mode='HTML')
        return
    update_balance(uid, -stake)
    casino_in_progress[uid] = True
    solo_game_stakes[uid] = stake
    data = {'items': ['🔒'] * 4, 'real': ['💀', '💀', '💰', '💰'],
            'stake': stake, 'golds': 0, 'gold_indices': [], 'finished': False, 'taken': False}
    random.shuffle(data['real'])
    chest_cache[uid] = data
    show_chest_game(cid, uid, is_new=True)


def show_chest_game(cid, uid, msg_id=None, is_new=False):
    data = chest_cache.get(uid)
    if not data:
        return
    items = data['items']
    stake = data['stake']
    golds = data['golds']
    finished = data.get('finished', False)
    gi_l = data.get('gold_indices', [])
    markup = types.InlineKeyboardMarkup(row_width=4)

    def gi(i):
        return ICO_GOLD if i in gi_l and gi_l.index(i) == 0 else ICO_GOLD2 if i in gi_l else ICO_GOLD

    btns = []
    for i in range(len(items)):
        if finished:
            ri = data['real'][i]
            if ri == '💰':
                btns.append(btn(' ', callback_data="ignore", icon=gi(i)))
            elif ri == '💀':
                btns.append(btn(' ', callback_data="ignore", icon=ICO_SKULL))
            else:
                btns.append(btn(' ', callback_data="ignore", icon=ICO_LOCK))
        else:
            if items[i] == '💰':
                btns.append(btn(' ', callback_data="ignore", icon=gi(i)))
            elif items[i] == '💀':
                btns.append(btn(' ', callback_data="ignore", icon=ICO_SKULL))
            else:
                btns.append(btn(f"{i+1}", callback_data=f"chest_{i}", style='primary', icon=ICO_CHEST))
    markup.add(*btns)
    if golds > 0 and not finished and not data.get('taken', False):
        markup.add(btn("ЗАБРАТЬ", callback_data="chest_take", style='success', icon=ICO_GOLD_BTN))
    if finished:
        if data.get('win', False):
            text = f"🎉 <b>ВЫИГРЫШ!</b> +{data.get('win_amount', 0):,} {EMO_NOX}"
        else:
            text = f"{EMO_SKULL} <b>ПРОИГРЫШ!</b> -{stake:,} {EMO_NOX}"
    else:
        if golds == 0:
            text = f"{EMO_CHEST} <b>ВЫБЕРИ СУНДУК</b>\n{EMO_NOX} Ставка: {stake:,}"
        elif golds == 1:
            text = f"{EMO_GOLD} <b>ЗОЛОТО!</b> {int(stake*1.5):,} (x1.5)\nЕщё или забери"
        else:
            text = f"{EMO_CHEST} <b>ВЫБЕРИ СУНДУК</b>"
    if is_new:
        safe_send(cid, text, parse_mode='HTML', reply_markup=markup)
    else:
        safe_edit(cid, msg_id, text, parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("chest_") and not call.data.startswith("chest_take"))
def chest_choice(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    data = chest_cache.get(uid)
    if not data or data.get('finished', False) or not casino_in_progress.get(uid, False):
        safe_answer(call.id, "⏳", show_alert=True)
        return
    try:
        idx = int(call.data.split("_")[1])
        items = data['items']
        real = data['real']
        stake = data['stake']
        if items[idx] in ('💰', '💀'):
            safe_answer(call.id, "Уже открыто", show_alert=True)
            return
        if real[idx] == '💰':
            data['golds'] += 1
            data.setdefault('gold_indices', []).append(idx)
            items[idx] = '💰'
            if data['golds'] == 1:
                safe_answer(call.id, "💰 +x1.5!")
                show_chest_game(cid, uid, mid)
                return
            elif data['golds'] == 2:
                wa = int(stake * 2)
                update_balance(uid, wa)
                data['finished'] = True
                data['win'] = True
                data['win_amount'] = wa
                casino_in_progress[uid] = False
                safe_answer(call.id, "🎉 x2!")
                show_chest_game(cid, uid, mid)
                clean_chest(uid)
                return
        else:
            items[idx] = '💀'
            data['finished'] = True
            data['win'] = False
            casino_in_progress[uid] = False
            safe_answer(call.id, "💀!")
            show_chest_game(cid, uid, mid)
            clean_chest(uid)
            return
    except Exception:
        safe_answer(call.id, "❌", show_alert=True)
        clean_chest(uid)


@bot.callback_query_handler(func=lambda call: call.data == "chest_take")
def chest_take(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    data = chest_cache.get(uid)
    if not data or data.get('finished', False) or data.get('taken', False):
        safe_answer(call.id, "⏳", show_alert=True)
        return
    try:
        stake = data['stake']
        win = int(stake * 1.5)
        update_balance(uid, win)
        data['finished'] = True
        data['win'] = True
        data['win_amount'] = win
        data['taken'] = True
        casino_in_progress[uid] = False
        safe_answer(call.id, f"✅ +{win:,}!")
        show_chest_game(cid, uid, mid)
        clean_chest(uid)
    except Exception:
        safe_answer(call.id, "❌", show_alert=True)
        clean_chest(uid)


def clean_chest(uid):
    chest_cache.pop(uid, None)
    casino_in_progress[uid] = False
    solo_game_stakes.pop(uid, None)


# ---------- ЭТАЖИ ----------

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('этажи'))
def cmd_floors_game(message):
    if check_pm_game(message):
        return
    uid = message.from_user.id
    cid = message.chat.id
    if casino_in_progress.get(uid, False):
        markup = types.InlineKeyboardMarkup()
        markup.add(btn("Сбросить", callback_data="reset_solo_games", style='primary'))
        safe_send(cid, f"{EMO_TIMER} Уже есть игра!", reply_markup=markup, parse_mode='HTML')
        return
    match = re.match(r'^этажи\s+(\S+)$', message.text.strip().lower())
    if not match:
        safe_send(cid, f"{EMO_BULB} <code>этажи [ставка]</code>", parse_mode='HTML')
        return
    user = get_or_create_user(uid, message.from_user.username, message.from_user.first_name)
    sa = match.group(1).strip()
    if sa == 'вб':
        stake = user['balance']
    else:
        try:
            stake = int(sa)
        except ValueError:
            safe_send(cid, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
    if stake < 1:
        safe_send(cid, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
        return
    if user['balance'] < stake:
        safe_send(cid, f"{EMO_BULB} Мало!", parse_mode='HTML')
        return
    update_balance(uid, -stake)
    casino_in_progress[uid] = True
    solo_game_stakes[uid] = stake
    fd = {'user_id': uid, 'stake': stake, 'floor': 1, 'multiplier': 1.0, 'finished': False, 'chat_id': cid, 'msg_id': None}
    show_floor_game(cid, fd, is_new=True)


def show_floor_game(cid, fd, msg_id=None, is_new=False):
    uid = fd['user_id']
    floor = fd['floor']
    mult = fd['multiplier']
    stake = fd['stake']
    if fd.get('finished', False):
        return
    pw = int(stake * mult)
    text = f"{EMO_FLOOR} ЭТАЖ {floor}\n{EMO_NOX} Ставка: {stake:,}\n{EMO_MULT} x{mult}\n{EMO_TROPHY} Выигрыш: {pw:,}"
    markup = types.InlineKeyboardMarkup(row_width=2)
    if floor >= 10:
        markup.add(btn("ЗАБРАТЬ", callback_data=f"floors_take_{uid}_{floor}_{stake}_{mult}", style='success', icon=ICO_GOLD_BTN))
    else:
        markup.add(btn("ПОДНЯТЬСЯ", callback_data=f"floors_up_{uid}_{floor}_{stake}_{mult}", style='primary', icon=ICO_BULB))
        markup.add(btn("ЗАБРАТЬ", callback_data=f"floors_take_{uid}_{floor}_{stake}_{mult}", style='success', icon=ICO_GOLD_BTN))
    if is_new:
        m = safe_send(cid, text, parse_mode='HTML', reply_markup=markup)
        if m:
            fd['msg_id'] = m.message_id
    elif msg_id:
        safe_edit(cid, msg_id, text, parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("floors_up_"))
def floors_up(call):
    p = call.data.split("_")
    uid = int(p[2])
    floor = int(p[3])
    stake = int(p[4])
    mult = float(p[5])
    if call.from_user.id != uid:
        safe_answer(call.id, "🖕 Не твоя!", show_alert=True)
        return
    lc = {1:15, 2:20, 3:25, 4:30, 5:35, 6:45, 7:55, 8:70, 9:85}
    if random.randint(1, 100) <= lc.get(floor, 0):
        casino_in_progress[uid] = False
        solo_game_stakes.pop(uid, None)
        safe_edit(call.message.chat.id, call.message.message_id,
                  f"{EMO_SKULL} БАХ! Упал!\nСтавка {stake:,} сгорела!", parse_mode='HTML')
        safe_answer(call.id, "💀!")
    else:
        nf = floor + 1
        mults = {2:1.2, 3:1.4, 4:1.7, 5:2.0, 6:2.5, 7:3.0, 8:4.0, 9:5.0, 10:10.0}
        nm = mults.get(nf, mult)
        fd = {'user_id': uid, 'stake': stake, 'floor': nf, 'multiplier': nm, 'finished': False,
              'chat_id': call.message.chat.id, 'msg_id': call.message.message_id}
        show_floor_game(call.message.chat.id, fd, call.message.message_id)
        safe_answer(call.id, "⬆️!")


@bot.callback_query_handler(func=lambda call: call.data.startswith("floors_take_"))
def floors_take(call):
    p = call.data.split("_")
    uid = int(p[2])
    stake = int(p[4])
    mult = float(p[5])
    if call.from_user.id != uid:
        safe_answer(call.id, "🖖 Не твоя!", show_alert=True)
        return
    wa = int(stake * mult)
    update_balance(uid, wa)
    casino_in_progress[uid] = False
    solo_game_stakes.pop(uid, None)
    safe_edit(call.message.chat.id, call.message.message_id,
              f"{EMO_GOLDTEXT} ЗАБРАЛ!\n+{wa:,} {EMO_NOX}! (x{mult})", parse_mode='HTML')
    safe_answer(call.id, f"✅ +{wa}!")


# ---------- РУЛЕТКА ----------

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('рулетка'))
def cmd_roulette_game(message):
    if check_pm_game(message):
        return
    if check_banned(message.from_user.id, message.chat.id):
        return
    match = re.match(r'^рулетка\s+(\S+)$', message.text.strip().lower())
    if not match:
        safe_send(message.chat.id, f"{EMO_BULB} <code>рулетка [ставка]</code>", parse_mode='HTML')
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    sa = match.group(1).strip()
    if sa == 'вб':
        stake = user['balance']
    else:
        try:
            stake = int(sa)
        except ValueError:
            safe_send(message.chat.id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
    if stake < 1:
        safe_send(message.chat.id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
        return
    if user['balance'] < stake:
        safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
        return
    if check_player_in_game(message.from_user.id):
        force_cleanup_player(message.from_user.id)
    ud = get_user_display(user)
    if message.reply_to_message:
        tid = message.reply_to_message.from_user.id
        tgt = get_or_create_user(tid, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
        if tid == user['user_id']:
            safe_send(message.chat.id, f"{EMO_BULB} Себе нельзя!", parse_mode='HTML')
            return
        if tgt['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
            return
        if check_player_in_game(tid):
            safe_send(message.chat.id, f"{EMO_BULB} Соперник в игре!", parse_mode='HTML')
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_roulette_{message.from_user.id}_{tid}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT),
                   btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_ROULETTE} {ud} → {get_user_display(tgt)}!\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'roulette', 'stake': stake, 'chat_id': message.chat.id}
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_roulette_open_{message.from_user.id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT),
                   btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_ROULETTE} {ud} ищет соперника!\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'roulette', 'stake': stake, 'chat_id': message.chat.id}


def start_roulette_match(cid, p1, p2, stake):
    add_player_to_game(p1['user_id'])
    add_player_to_game(p2['user_id'])
    ct = random.choice([p1['user_id'], p2['user_id']])
    p1d, p2d = get_user_display(p1), get_user_display(p2)
    gd = {'p1_id': p1['user_id'], 'p2_id': p2['user_id'], 'stake': stake, 'current_turn': ct,
          'shot_count': 0, 'finished': False, 'chat_id': cid}
    m = safe_send(cid, f"{EMO_ROULETTE} РУЛЕТКА!\n{p1d} {EMO_VS} {p2d}\n{EMO_NOX} {stake:,}\nХодит: {get_user_display_by_id(ct)}", parse_mode='HTML')
    if not m:
        return
    gmid = m.message_id
    active_games[cid] = active_games.get(cid, {})
    active_games[cid][gmid] = gd
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("ВЫСТРЕЛИТЬ", callback_data=f"roulette_shoot_{gmid}_{ct}", style='danger', icon=ICO_ROULETTE))
    safe_edit(cid, gmid, f"{EMO_ROULETTE} РУЛЕТКА!\n{p1d} {EMO_VS} {p2d}\n{EMO_NOX} {stake:,}\nХодит: {get_user_display_by_id(ct)}",
              reply_markup=markup, parse_mode='HTML')
    start_timer(cid, gmid, game_type='roulette', timeout=60)


@bot.callback_query_handler(func=lambda call: call.data.startswith("roulette_shoot_"))
def roulette_shoot(call):
    p = call.data.split("_")
    gmid = int(p[2])
    tid = int(p[3])
    uid = call.from_user.id
    cid = call.message.chat.id
    if gmid not in active_games.get(cid, {}):
        safe_answer(call.id, "❌", show_alert=True)
        return
    g = active_games[cid][gmid]
    if g.get('finished', False) or uid != tid or uid != g['current_turn']:
        safe_answer(call.id, "❌ Не твой ход!", show_alert=True)
        return
    cancel_timer(cid, gmid)
    g['shot_count'] += 1
    if random.randint(1, 6) == 1:
        lid = uid
        wid = g['p1_id'] if uid == g['p2_id'] else g['p2_id']
        g['finished'] = True
        wa = g['stake'] * 2
        update_balance(wid, wa)
        update_streak(wid, True, g['stake'])
        update_streak(lid, False, g['stake'])
        update_game_stats(wid, 'roulette', True)
        update_game_stats(lid, 'roulette', False)
        safe_edit(cid, gmid, f"{EMO_BOOM} БАХ! {get_user_display_by_id(lid)} проиграл!\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,} {EMO_NOX}!", parse_mode='HTML')
        del active_games[cid][gmid]
        remove_player_from_game(wid)
        remove_player_from_game(lid)
        safe_answer(call.id, "💥!")
    else:
        safe_answer(call.id, "🔫 Холостой!")
        g['current_turn'] = g['p1_id'] if g['current_turn'] == g['p2_id'] else g['p2_id']
        nd = get_user_display_by_id(g['current_turn'])
        markup = types.InlineKeyboardMarkup()
        markup.add(btn("ВЫСТРЕЛИТЬ", callback_data=f"roulette_shoot_{gmid}_{g['current_turn']}", style='danger', icon=ICO_ROULETTE))
        safe_edit(cid, gmid, f"{EMO_ROULETTE} Выстрел {g['shot_count']}\nХодит: {nd}", reply_markup=markup, parse_mode='HTML')
        start_timer(cid, gmid, game_type='roulette', timeout=60)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_roulette_open_"))
def join_roulette_open(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    hid = int(p[3])
    stake = int(p[4])
    mid = int(p[5])
    uid = call.from_user.id
    with invite_lock:
        if mid not in invites:
            return
        inv = invites[mid]
        if uid == hid or inv['game_type'] != 'roulette':
            safe_answer(call.id, "❌", show_alert=True)
            return
        if check_player_in_game(uid):
            force_cleanup_player(uid)
        del invites[mid]
    h = get_or_create_user(hid, "", "")
    gu = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or gu['balance'] < stake:
        safe_answer(call.id, "❌ Мало!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    start_roulette_match(call.message.chat.id, h, gu, stake)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_roulette_"))
def join_roulette(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    hid = int(p[2])
    tid = int(p[3])
    stake = int(p[4])
    mid = int(p[5])
    uid = call.from_user.id
    with invite_lock:
        if mid not in invites:
            return
        inv = invites[mid]
        if uid != tid or inv['game_type'] != 'roulette':
            safe_answer(call.id, "Не твой!", show_alert=True)
            return
        if check_player_in_game(uid):
            force_cleanup_player(uid)
        del invites[mid]
    h = get_or_create_user(hid, "", "")
    gu = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or gu['balance'] < stake:
        safe_answer(call.id, "❌ Мало!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    start_roulette_match(call.message.chat.id, h, gu, stake)


# ---------- ОРЁЛ / РЕШКА ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith(('орел', 'орёл', 'решка')))
def cmd_eagle_game(message):
    if check_pm_game(message):
        return
    try:
        if check_banned(message.from_user.id, message.chat.id):
            return
        match = re.match(r'^(орел|орёл|решка)\s+(\S+)$', message.text.strip().lower())
        if not match:
            safe_send(message.chat.id, f"{EMO_BULB} <code>орел [ставка]</code>", parse_mode='HTML')
            return
        user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        sa = match.group(2).strip()
        if sa == 'вб':
            stake = user['balance']
        else:
            try:
                stake = int(sa)
            except ValueError:
                safe_send(message.chat.id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
                return
        if stake < 1:
            safe_send(message.chat.id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
            return
        if user['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
            return
        if check_player_in_game(message.from_user.id):
            force_cleanup_player(message.from_user.id)
        ud = get_user_display(user)
        if message.reply_to_message:
            tid = message.reply_to_message.from_user.id
            tgt = get_or_create_user(tid, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
            if tid == user['user_id']:
                safe_send(message.chat.id, f"{EMO_BULB} Себе!", parse_mode='HTML')
                return
            if tgt['balance'] < stake:
                safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
                return
            if check_player_in_game(tid):
                safe_send(message.chat.id, f"{EMO_BULB} Соперник в игре!", parse_mode='HTML')
                return
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(btn("Принять", callback_data=f"join_eg_dir:{user['user_id']}:{tid}:{stake}", style='success', icon=ICO_ACCEPT),
                       btn("Отмена", callback_data=f"cancel_eg:{user['user_id']}", style='danger', icon=ICO_CANCEL))
            m = safe_send(message.chat.id, f"{EMO_EAGLE} {ud} → {get_user_display(tgt)}!\nОрёл/Решка\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        else:
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(btn("Принять", callback_data=f"join_eg_open:{user['user_id']}:{stake}", style='success', icon=ICO_ACCEPT),
                       btn("Отмена", callback_data=f"cancel_eg:{user['user_id']}", style='danger', icon=ICO_CANCEL))
            m = safe_send(message.chat.id, f"{EMO_EAGLE} {ud} ищет соперника!\nОрёл/Решка\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        if m:
            with invite_lock:
                invites[m.message_id] = {'host_id': user['user_id'], 'game_type': 'eagle', 'stake': stake, 'chat_id': message.chat.id}
    except Exception as e:
        safe_send(message.chat.id, f"❌ {e}", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_eg_dir:"))
def join_eagle_direct(call):
    safe_answer(call.id)
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    _, hid, tid, st = call.data.split(":")
    hid, tid, st = int(hid), int(tid), int(st)
    if call.from_user.id != tid:
        safe_send(call.message.chat.id, "❌ Не тебе!", parse_mode='HTML')
        return
    with invite_lock:
        invites.pop(call.message.message_id, None)
    start_eagle_duel(call, hid, tid, st)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_eg_open:"))
def join_eagle_open(call):
    safe_answer(call.id)
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    _, hid, st = call.data.split(":")
    hid, st = int(hid), int(st)
    if call.from_user.id == hid:
        safe_send(call.message.chat.id, "❌ Себе!", parse_mode='HTML')
        return
    with invite_lock:
        if call.message.message_id not in invites:
            safe_send(call.message.chat.id, "❌ Недоступна!", parse_mode='HTML')
            return
        del invites[call.message.message_id]
    start_eagle_duel(call, hid, call.from_user.id, st)


@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_eg:"))
def cancel_eagle_invite(call):
    safe_answer(call.id)
    hid = int(call.data.split(":")[1])
    if call.from_user.id != hid:
        return
    with invite_lock:
        invites.pop(call.message.message_id, None)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass


def start_eagle_duel(call, hid, gid, stake):
    h = get_or_create_user(hid, "", "")
    g = get_or_create_user(gid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or g['balance'] < stake:
        safe_send(call.message.chat.id, "❌ Мало!", parse_mode='HTML')
        return
    if check_player_in_game(hid):
        force_cleanup_player(hid)
    if check_player_in_game(gid):
        force_cleanup_player(gid)
    if random.random() < 0.5:
        cid, gsi = hid, gid
    else:
        cid, gsi = gid, hid
    cd, gd = get_user_display_by_id(cid), get_user_display_by_id(gsi)
    update_balance(hid, -stake)
    update_balance(gid, -stake)
    add_player_to_game(cid)
    add_player_to_game(gsi)
    game_id = f"e{int(time.time())}{random.randint(100,999)}"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(btn("Орёл", callback_data=f"egch:{game_id}:1", style='primary', icon=ICO_EAGLE),
               btn("Решка", callback_data=f"egch:{game_id}:2", style='success', icon=ICO_EAGLE))
    safe_edit(call.message.chat.id, call.message.message_id,
              f"{EMO_EAGLE} Орёл/Решка!\n{EMO_NOX} {stake:,}\n🎯 {cd} ВЫБИРАЕТ\n🤔 {gd} УГАДЫВАЕТ",
              parse_mode='HTML', reply_markup=markup)
    if call.message.chat.id not in active_games:
        active_games[call.message.chat.id] = {}
    active_games[call.message.chat.id][game_id] = {'game_type': 'eagle', 'chooser_id': cid, 'guesser_id': gsi,
                                                    'stake': stake, 'state': 'choose',
                                                    'msg_id': call.message.message_id, 'finished': False}
    start_timer(call.message.chat.id, call.message.message_id, game_type='eagle_choice', timeout=60)


@bot.callback_query_handler(func=lambda call: call.data.startswith("egch:"))
def eagle_choose(call):
    safe_answer(call.id)
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    _, gid, cn = call.data.split(":")
    cn = int(cn)
    cid = call.message.chat.id
    uid = call.from_user.id
    if cid not in active_games or gid not in active_games[cid]:
        return
    g = active_games[cid][gid]
    if g.get('finished', False) or g.get('state') != 'choose' or uid != g['chooser_id']:
        return
    ch = 'орёл' if cn == 1 else 'решка'
    g['state'] = 'chosen'
    g['choice'] = ch
    cancel_timer(cid, g['msg_id'])
    cd, gd = get_user_display_by_id(g['chooser_id']), get_user_display_by_id(g['guesser_id'])
    ggid = f"e{int(time.time())}{random.randint(100,999)}"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(btn("Орёл", callback_data=f"eggs:{ggid}:1", style='primary', icon=ICO_EAGLE),
               btn("Решка", callback_data=f"eggs:{ggid}:2", style='success', icon=ICO_EAGLE))
    safe_edit(cid, g['msg_id'], f"{EMO_EAGLE} {cd} загадал!\n🤔 {gd} угадай!", parse_mode='HTML', reply_markup=markup)
    c_id, gs_id, st, mid = g['chooser_id'], g['guesser_id'], g['stake'], g['msg_id']
    del active_games[cid][gid]
    active_games[cid][ggid] = {'game_type': 'eagle_guess', 'chooser_id': c_id, 'guesser_id': gs_id,
                               'stake': st, 'choice': ch, 'msg_id': mid, 'finished': False}
    start_timer(cid, mid, game_type='eagle_guess', timeout=60)


@bot.callback_query_handler(func=lambda call: call.data.startswith("eggs:"))
def eagle_guess(call):
    safe_answer(call.id)
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    _, gid, gn = call.data.split(":")
    gn = int(gn)
    cid = call.message.chat.id
    uid = call.from_user.id
    if cid not in active_games or gid not in active_games[cid]:
        return
    g = active_games[cid][gid]
    if g.get('finished', False) or uid != g['guesser_id']:
        return
    cancel_timer(cid, g['msg_id'])
    g['finished'] = True
    c_id, gs_id, st = g['chooser_id'], g['guesser_id'], g['stake']
    sc = g['choice']
    guess = 'орёл' if gn == 1 else 'решка'
    if guess == sc:
        wid, lid = gs_id, c_id
        txt = f"🎯 {get_user_display_by_id(c_id)} загадал {sc.capitalize()}\n🤔 {get_user_display_by_id(gs_id)} УГАДАЛ!"
    else:
        wid, lid = c_id, gs_id
        txt = f"🎯 {get_user_display_by_id(c_id)} загадал {sc.capitalize()}\n🤔 {get_user_display_by_id(gs_id)} не угадал!"
    wa = st * 2
    update_balance(wid, wa)
    update_streak(wid, True, st)
    update_streak(lid, False, st)
    update_game_stats(wid, 'eagle', True)
    update_game_stats(lid, 'eagle', False)
    safe_edit(cid, g['msg_id'], f"{EMO_EAGLE} <b>РЕЗУЛЬТАТ:</b>\n\n{txt}\n\n{EMO_CROWN} {get_user_display_by_id(wid)} +{st:,} {EMO_NOX}!",
              parse_mode='HTML', reply_markup=None)
    remove_player_from_game(wid)
    remove_player_from_game(lid)
    active_games[cid].pop(gid, None)


# ---------- КОСТИ ----------

@bot.message_handler(func=lambda m: m.text and (m.text.strip().lower().startswith('кости') or m.text.strip().lower().startswith('кубики')))
def cmd_dice_game(message):
    if check_pm_game(message):
        return
    if check_banned(message.from_user.id, message.chat.id):
        return
    match = re.match(r'^(кости|кубики)\s+(\S+)$', message.text.strip().lower())
    if not match:
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    sa = match.group(2).strip()
    if sa == 'вб':
        stake = user['balance']
    else:
        try:
            stake = int(sa)
        except ValueError:
            safe_send(message.chat.id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
    if stake < 1:
        safe_send(message.chat.id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
        return
    if user['balance'] < stake:
        safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
        return
    if check_player_in_game(message.from_user.id):
        force_cleanup_player(message.from_user.id)
    ud = get_user_display(user)
    if message.reply_to_message:
        tid = message.reply_to_message.from_user.id
        tgt = get_or_create_user(tid, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
        if tid == user['user_id']:
            safe_send(message.chat.id, f"{EMO_BULB} Себе!", parse_mode='HTML')
            return
        if tgt['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
            return
        if check_player_in_game(tid):
            safe_send(message.chat.id, f"{EMO_BULB} Соперник в игре!", parse_mode='HTML')
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_dice_{message.from_user.id}_{tid}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT),
                   btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_DICE} {ud} → {get_user_display(tgt)}!\nКости 1на1\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'dice', 'stake': stake, 'chat_id': message.chat.id}
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_dice_open_{message.from_user.id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT),
                   btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_DICE} {ud} ищет соперника!\nКости 1на1\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'dice', 'stake': stake, 'chat_id': message.chat.id}


def run_dice_match_thread(cid, p1, p2, stake, mid):
    try:
        p1d, p2d = get_user_display(p1), get_user_display(p2)
        safe_send(cid, f"{EMO_DICE} {p1d} бросает...", parse_mode='HTML')
        try:
            d1 = bot.send_dice(cid).dice.value
        except Exception:
            finalize_game(cid, p1['user_id'], p2['user_id'], stake, 'dice', 'error', mid)
            return
        time.sleep(3)
        safe_send(cid, f"{EMO_DICE} {p2d} бросает...", parse_mode='HTML')
        try:
            d2 = bot.send_dice(cid).dice.value
        except Exception:
            finalize_game(cid, p1['user_id'], p2['user_id'], stake, 'dice', 'error', mid)
            return
        time.sleep(2)
        if d1 > d2:
            finalize_game(cid, p1['user_id'], p2['user_id'], stake, 'dice', 'win', mid)
        elif d2 > d1:
            finalize_game(cid, p2['user_id'], p1['user_id'], stake, 'dice', 'win', mid)
        else:
            safe_send(cid, f"{EMO_HANDSHAKE} Ничья ({d1}:{d2})! Перекидываем...", parse_mode='HTML')
            time.sleep(2)
            run_dice_match_thread(cid, p1, p2, stake, mid)
    except Exception:
        pass


def run_dice_match(cid, p1, p2, stake, mid):
    add_player_to_game(p1['user_id'])
    add_player_to_game(p2['user_id'])
    threading.Thread(target=run_dice_match_thread, args=(cid, p1, p2, stake, mid), daemon=True).start()


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_dice_open_"))
def join_dice_open(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    hid = int(p[3])
    stake = int(p[4])
    mid = int(p[5])
    uid = call.from_user.id
    with invite_lock:
        if mid not in invites:
            return
        inv = invites[mid]
        if uid == hid or inv['game_type'] != 'dice':
            safe_answer(call.id, "❌", show_alert=True)
            return
        if check_player_in_game(uid):
            force_cleanup_player(uid)
        del invites[mid]
    h = get_or_create_user(hid, "", "")
    gu = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or gu['balance'] < stake:
        safe_answer(call.id, "❌ Мало!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    run_dice_match(call.message.chat.id, h, gu, stake, mid)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_dice_"))
def join_dice(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    hid = int(p[2])
    tid = int(p[3])
    stake = int(p[4])
    mid = int(p[5])
    uid = call.from_user.id
    with invite_lock:
        if mid not in invites:
            return
        inv = invites[mid]
        if uid != tid or inv['game_type'] != 'dice':
            safe_answer(call.id, "Не твой!", show_alert=True)
            return
        if check_player_in_game(uid):
            force_cleanup_player(uid)
        del invites[mid]
    h = get_or_create_user(hid, "", "")
    gu = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or gu['balance'] < stake:
        safe_answer(call.id, "❌ Мало!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    run_dice_match(call.message.chat.id, h, gu, stake, mid)


# ---------- ЦУЕФА (КНБ) ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith('цуефа'))
def cmd_rps_game(message):
    if check_pm_game(message):
        return
    if check_banned(message.from_user.id, message.chat.id):
        return
    match = re.match(r'^цуефа\s+(\S+)$', message.text.strip().lower())
    if not match:
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    sa = match.group(1).strip()
    if sa == 'вб':
        stake = user['balance']
    else:
        try:
            stake = int(sa)
        except ValueError:
            safe_send(message.chat.id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
    if stake < 1:
        safe_send(message.chat.id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
        return
    if user['balance'] < stake:
        safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
        return
    if check_player_in_game(message.from_user.id):
        force_cleanup_player(message.from_user.id)
    ud = get_user_display(user)
    if message.reply_to_message:
        tid = message.reply_to_message.from_user.id
        tgt = get_or_create_user(tid, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
        if tid == user['user_id']:
            safe_send(message.chat.id, f"{EMO_BULB} Себе!", parse_mode='HTML')
            return
        if tgt['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
            return
        if check_player_in_game(tid):
            safe_send(message.chat.id, f"{EMO_BULB} Соперник в игре!", parse_mode='HTML')
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_rps_{message.from_user.id}_{tid}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT),
                   btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_ROCK} {ud} → {get_user_display(tgt)}!\nКНБ\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'rps', 'stake': stake, 'chat_id': message.chat.id}
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_rps_open_{message.from_user.id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT),
                   btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_ROCK} {ud} ищет соперника!\nКНБ\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'rps', 'stake': stake, 'chat_id': message.chat.id}


def start_rps_match(cid, p1, p2, stake):
    add_player_to_game(p1['user_id'])
    add_player_to_game(p2['user_id'])
    p1d, p2d = get_user_display(p1), get_user_display(p2)
    markup = types.InlineKeyboardMarkup(row_width=3)
    m = safe_send(cid, f"{EMO_TIMER} Ход!")
    if not m:
        return
    markup.add(btn("Камень", callback_data=f"play_rps_{m.message_id}_🪨", style='primary', icon=ICO_ROCK))
    markup.add(btn("Ножницы", callback_data=f"play_rps_{m.message_id}_✂️", style='danger', icon=ICO_SCISSORS))
    markup.add(btn("Бумага", callback_data=f"play_rps_{m.message_id}_📄", style='success', icon=ICO_PAPER))
    active_games[cid] = active_games.get(cid, {})
    active_games[cid][m.message_id] = {'p1_id': p1['user_id'], 'p2_id': p2['user_id'],
                                        'p1_choice': None, 'p2_choice': None, 'stake': stake,
                                        'game_type': 'rps', 'finished': False, 'chat_id': cid, 'msg_id': m.message_id}
    safe_edit(cid, m.message_id, f"{EMO_ROCK} {p1d} {EMO_VS} {p2d}!\n{EMO_NOX} {stake:,}\n{EMO_TIMER} 60с!",
              reply_markup=markup, parse_mode='HTML')
    start_timer(cid, m.message_id, game_type='rps', timeout=60)


def check_rps_result(cid, mid):
    g = active_games[cid][mid]
    if g.get('finished', False) or not (g['p1_choice'] and g['p2_choice']):
        return
    cancel_timer(cid, mid)
    c1, c2 = g['p1_choice'], g['p2_choice']
    rules = {"🪨": "✂️", "✂️": "📄", "📄": "🪨"}
    p1d, p2d = get_user_display_by_id(g['p1_id']), get_user_display_by_id(g['p2_id'])
    cd = {"🪨": EMO_ROCK, "✂️": EMO_SCISSORS, "📄": EMO_PAPER}
    if c1 == c2:
        update_balance(g['p1_id'], g['stake'])
        update_balance(g['p2_id'], g['stake'])
        g['p1_choice'] = None
        g['p2_choice'] = None
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(btn("Камень", callback_data=f"play_rps_{mid}_🪨", style='primary', icon=ICO_ROCK))
        markup.add(btn("Ножницы", callback_data=f"play_rps_{mid}_✂️", style='danger', icon=ICO_SCISSORS))
        markup.add(btn("Бумага", callback_data=f"play_rps_{mid}_📄", style='success', icon=ICO_PAPER))
        safe_edit(cid, mid, f"{EMO_HANDSHAKE} Ничья! {cd[c1]}", reply_markup=markup, parse_mode='HTML')
        start_timer(cid, mid, game_type='rps', timeout=60)
    else:
        if rules[c1] == c2:
            wid, lid = g['p1_id'], g['p2_id']
        else:
            wid, lid = g['p2_id'], g['p1_id']
        g['finished'] = True
        wa = g['stake'] * 2
        update_balance(wid, wa)
        update_streak(wid, True, g['stake'])
        update_streak(lid, False, g['stake'])
        update_game_stats(wid, 'rps', True)
        update_game_stats(lid, 'rps', False)
        try:
            bot.delete_message(cid, mid)
        except Exception:
            pass
        safe_send(cid, f"{EMO_TROPHY} {p1d}: {cd[c1]}\n{EMO_TROPHY} {p2d}: {cd[c2]}\n\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,} {EMO_NOX}!", parse_mode='HTML')
        del active_games[cid][mid]
        remove_player_from_game(wid)
        remove_player_from_game(lid)


@bot.callback_query_handler(func=lambda call: call.data.startswith("play_rps_"))
def play_rps(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    mid = int(p[2])
    ch = p[3]
    cid = call.message.chat.id
    uid = call.from_user.id
    if mid not in active_games.get(cid, {}):
        return
    g = active_games[cid][mid]
    if g.get('finished', False):
        return
    if uid == g['p1_id'] and not g['p1_choice']:
        g['p1_choice'] = ch
        safe_answer(call.id, f"Ты: {ch}!")
    elif uid == g['p2_id'] and not g['p2_choice']:
        g['p2_choice'] = ch
        safe_answer(call.id, f"Ты: {ch}!")
    else:
        return
    check_rps_result(cid, mid)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_rps_open_"))
def join_rps_open(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    hid = int(p[3])
    stake = int(p[4])
    mid = int(p[5])
    uid = call.from_user.id
    with invite_lock:
        if mid not in invites:
            return
        inv = invites[mid]
        if uid == hid or inv['game_type'] != 'rps':
            safe_answer(call.id, "❌", show_alert=True)
            return
        if check_player_in_game(uid):
            force_cleanup_player(uid)
        del invites[mid]
    h = get_or_create_user(hid, "", "")
    gu = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or gu['balance'] < stake:
        safe_answer(call.id, "❌ Мало!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    start_rps_match(call.message.chat.id, h, gu, stake)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_rps_"))
def join_rps(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    hid = int(p[2])
    tid = int(p[3])
    stake = int(p[4])
    mid = int(p[5])
    uid = call.from_user.id
    with invite_lock:
        if mid not in invites:
            return
        inv = invites[mid]
        if uid != tid or inv['game_type'] != 'rps':
            safe_answer(call.id, "Не твой!", show_alert=True)
            return
        if check_player_in_game(uid):
            force_cleanup_player(uid)
        del invites[mid]
    h = get_or_create_user(hid, "", "")
    gu = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or gu['balance'] < stake:
        safe_answer(call.id, "❌ Мало!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    start_rps_match(call.message.chat.id, h, gu, stake)


# ---------- КРЕСТИКИ-НОЛИКИ ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith('крестики'))
def cmd_ttt_game(message):
    if check_pm_game(message):
        return
    if check_banned(message.from_user.id, message.chat.id):
        return
    match = re.match(r'^крестики\s+(\S+)$', message.text.strip().lower())
    if not match:
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    sa = match.group(1).strip()
    if sa == 'вб':
        stake = user['balance']
    else:
        try:
            stake = int(sa)
        except ValueError:
            safe_send(message.chat.id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
    if stake < 1:
        safe_send(message.chat.id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
        return
    if user['balance'] < stake:
        safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
        return
    if check_player_in_game(message.from_user.id):
        force_cleanup_player(message.from_user.id)
    ud = get_user_display(user)
    if message.reply_to_message:
        tid = message.reply_to_message.from_user.id
        tgt = get_or_create_user(tid, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
        if tid == user['user_id']:
            safe_send(message.chat.id, f"{EMO_BULB} Себе!", parse_mode='HTML')
            return
        if tgt['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
            return
        if check_player_in_game(tid):
            safe_send(message.chat.id, f"{EMO_BULB} Соперник в игре!", parse_mode='HTML')
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_ttt_{message.from_user.id}_{tid}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT),
                   btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_TTT_INVITE} {ud} → {get_user_display(tgt)}!\nКрестики-Нолики\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'ttt', 'stake': stake, 'chat_id': message.chat.id}
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_ttt_open_{message.from_user.id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT),
                   btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_TTT_INVITE} {ud} ищет соперника!\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'ttt', 'stake': stake, 'chat_id': message.chat.id}


def start_ttt_match(cid, p1, p2, stake):
    add_player_to_game(p1['user_id'])
    add_player_to_game(p2['user_id'])
    board = ['⬜'] * 9
    p1d, p2d = get_user_display(p1), get_user_display(p2)
    p1n = get_or_create_user(p1['user_id'], "", "")
    p2n = get_or_create_user(p2['user_id'], "", "")
    if p1n['balance'] > p2n['balance']:
        first, fd, extra = 'X', p1d, f"({p1d} больше)"
    elif p2n['balance'] > p1n['balance']:
        first, fd, extra = 'O', p2d, f"({p2d} больше)"
    else:
        first = random.choice(['X', 'O'])
        fd = p1d if first == 'X' else p2d
        extra = "(равно)"
    m = safe_send(cid, f"{EMO_TTT_INVITE} Поле...")
    if not m:
        return
    active_games[cid] = active_games.get(cid, {})
    active_games[cid][m.message_id] = {'p1_id': p1['user_id'], 'p2_id': p2['user_id'], 'board': board, 'turn': first,
                                        'stake': stake, 'finished': False, 'game_type': 'ttt', 'processing': False,
                                        'chat_id': cid, 'msg_id': m.message_id}
    fs = EMO_TTT_X if first == 'X' else EMO_TTT_O
    safe_edit(cid, m.message_id, f"{EMO_TTT_INVITE} {p1d} {EMO_VS} {p2d}\n{EMO_NOX} {stake:,}\nХодит: {fd} {fs} {extra}",
              reply_markup=gen_ttt_board(board, m.message_id), parse_mode='HTML')
    start_timer(cid, m.message_id, game_type='ttt', timeout=60)


def gen_ttt_board(board, mid):
    markup = types.InlineKeyboardMarkup(row_width=3)
    syms = {0: '1️⃣', 1: '2️⃣', 2: '3️⃣', 3: '4️⃣', 4: '5️⃣', 5: '6️⃣', 6: '7️⃣', 7: '8️⃣', 8: '9️⃣'}
    btns = []
    for i, cell in enumerate(board):
        if cell == '❌':
            btns.append(btn(' ', callback_data="ignore", icon=ICO_TTT_X))
        elif cell == '⭕':
            btns.append(btn(' ', callback_data="ignore", icon=ICO_TTT_O))
        else:
            btns.append(btn(syms[i], callback_data=f"click_ttt_{mid}_{i}", style='primary'))
    for ch in [btns[i:i+3] for i in range(0, 9, 3)]:
        markup.add(*ch)
    markup.add(btn("СДАТЬСЯ", callback_data=f"surrender_ttt_{mid}", style='danger', icon=ICO_SURRENDER))
    return markup


def check_ttt_winner(b, t):
    board = ['X' if c == '❌' else 'O' if c == '⭕' else ' ' for c in b]
    s = 'X' if t == 'X' else 'O'
    for ln in [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]:
        if board[ln[0]] == board[ln[1]] == board[ln[2]] == s:
            return True
    return False


@bot.callback_query_handler(func=lambda call: call.data.startswith("click_ttt_"))
def click_ttt(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    mid = int(p[2])
    idx = int(p[3])
    cid = call.message.chat.id
    uid = call.from_user.id
    if mid not in active_games.get(cid, {}):
        return
    g = active_games[cid][mid]
    if g.get('finished', False) or g.get('processing', False):
        return
    g['processing'] = True
    try:
        ct = g['p1_id'] if g['turn'] == 'X' else g['p2_id']
        if uid != ct or g['board'][idx] != '⬜':
            return
        cancel_timer(cid, mid)
        g['board'][idx] = '❌' if g['turn'] == 'X' else '⭕'
        if check_ttt_winner(g['board'], g['turn']):
            wid = g['p1_id'] if g['turn'] == 'X' else g['p2_id']
            lid = g['p2_id'] if g['turn'] == 'X' else g['p1_id']
            g['finished'] = True
            wa = g['stake'] * 2
            update_balance(wid, wa)
            update_streak(wid, True, g['stake'])
            update_streak(lid, False, g['stake'])
            update_game_stats(wid, 'ttt', True)
            update_game_stats(lid, 'ttt', False)
            safe_edit(cid, mid, f"{EMO_TROPHY} {get_user_display_by_id(wid)} ПОБЕДИЛ! +{wa - g['stake']:,} {EMO_NOX}!", parse_mode='HTML')
            del active_games[cid][mid]
            remove_player_from_game(wid)
            remove_player_from_game(lid)
        elif '⬜' not in g['board']:
            update_balance(g['p1_id'], g['stake'])
            update_balance(g['p2_id'], g['stake'])
            safe_edit(cid, mid, f"{EMO_HANDSHAKE} Ничья!")
            del active_games[cid][mid]
            remove_player_from_game(g['p1_id'])
            remove_player_from_game(g['p2_id'])
        else:
            g['turn'] = 'O' if g['turn'] == 'X' else 'X'
            nid = g['p1_id'] if g['turn'] == 'X' else g['p2_id']
            ns = EMO_TTT_X if g['turn'] == 'X' else EMO_TTT_O
            safe_edit(cid, mid, f"{EMO_TTT_INVITE} Ходит: {get_user_display_by_id(nid)} {ns}",
                      reply_markup=gen_ttt_board(g['board'], mid), parse_mode='HTML')
            start_timer(cid, mid, game_type='ttt', timeout=60)
    except Exception as e:
        print(f"[TTT] {e}")
    g['processing'] = False


@bot.callback_query_handler(func=lambda call: call.data.startswith("surrender_ttt_"))
def surrender_ttt(call):
    safe_answer(call.id, "🏳️")
    p = call.data.split("_")
    mid = int(p[2])
    cid = call.message.chat.id
    uid = call.from_user.id
    if mid not in active_games.get(cid, {}):
        return
    g = active_games[cid][mid]
    if g.get('finished', False):
        return
    if uid == g['p1_id']:
        sid, wid = g['p1_id'], g['p2_id']
    elif uid == g['p2_id']:
        sid, wid = g['p2_id'], g['p1_id']
    else:
        return
    cancel_timer(cid, mid)
    g['finished'] = True
    wa = g['stake'] * 2
    update_balance(wid, wa)
    update_streak(wid, True, g['stake'])
    update_streak(sid, False, g['stake'])
    update_game_stats(wid, 'ttt', True)
    update_game_stats(sid, 'ttt', False)
    safe_edit(cid, mid, f"{EMO_SURRENDER} {get_user_display_by_id(sid)} СДАЛСЯ!\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,} {EMO_NOX}!",
              parse_mode='HTML')
    del active_games[cid][mid]
    remove_player_from_game(wid)
    remove_player_from_game(sid)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_ttt_open_"))
def join_ttt_open(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    hid = int(p[3])
    stake = int(p[4])
    mid = int(p[5])
    uid = call.from_user.id
    with invite_lock:
        if mid not in invites:
            return
        inv = invites[mid]
        if uid == hid or inv['game_type'] != 'ttt':
            safe_answer(call.id, "❌", show_alert=True)
            return
        if check_player_in_game(uid):
            force_cleanup_player(uid)
        del invites[mid]
    h = get_or_create_user(hid, "", "")
    gu = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or gu['balance'] < stake:
        safe_answer(call.id, "❌ Мало!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    start_ttt_match(call.message.chat.id, h, gu, stake)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_ttt_"))
def join_ttt(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    hid = int(p[2])
    tid = int(p[3])
    stake = int(p[4])
    mid = int(p[5])
    uid = call.from_user.id
    with invite_lock:
        if mid not in invites:
            return
        inv = invites[mid]
        if uid != tid or inv['game_type'] != 'ttt':
            safe_answer(call.id, "Не твой!", show_alert=True)
            return
        if check_player_in_game(uid):
            force_cleanup_player(uid)
        del invites[mid]
    h = get_or_create_user(hid, "", "")
    gu = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or gu['balance'] < stake:
        safe_answer(call.id, "❌ Мало!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    start_ttt_match(call.message.chat.id, h, gu, stake)


# ---------- МИНЫ ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith('мины'))
def cmd_mines_game(message):
    if check_pm_game(message):
        return
    if check_banned(message.from_user.id, message.chat.id):
        return
    match = re.match(r'^мины\s+(\S+)$', message.text.strip().lower())
    if not match:
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    sa = match.group(1).strip()
    if sa == 'вб':
        stake = user['balance']
    else:
        try:
            stake = int(sa)
        except ValueError:
            safe_send(message.chat.id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
    if stake < 1:
        safe_send(message.chat.id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
        return
    if user['balance'] < stake:
        safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
        return
    if check_player_in_game(message.from_user.id):
        force_cleanup_player(message.from_user.id)
    ud = get_user_display(user)
    if message.reply_to_message:
        tid = message.reply_to_message.from_user.id
        tgt = get_or_create_user(tid, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
        if tid == user['user_id']:
            safe_send(message.chat.id, f"{EMO_BULB} Себе!", parse_mode='HTML')
            return
        if tgt['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
            return
        if check_player_in_game(tid):
            safe_send(message.chat.id, f"{EMO_BULB} Соперник в игре!", parse_mode='HTML')
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_mines_{message.from_user.id}_{tid}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT),
                   btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_MINE} {ud} → {get_user_display(tgt)}!\nМинное поле 5x5\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'mines', 'stake': stake, 'chat_id': message.chat.id}
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_mines_open_{message.from_user.id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT),
                   btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_MINE} {ud} ищет соперника!\nМинное поле 5x5\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'mines', 'stake': stake, 'chat_id': message.chat.id}


def start_mines_match(cid, p1, p2, stake):
    add_player_to_game(p1['user_id'])
    add_player_to_game(p2['user_id'])
    board = ['⬜'] * 25
    mines = [False] * 25
    for i in random.sample(range(25), 6):
        mines[i] = True
    p1n = get_or_create_user(p1['user_id'], "", "")
    p2n = get_or_create_user(p2['user_id'], "", "")
    p1d, p2d = get_user_display(p1), get_user_display(p2)
    if p1n['balance'] > p2n['balance']:
        fp, fd, extra = 1, p1d, f"({p1d} больше)"
    elif p2n['balance'] > p1n['balance']:
        fp, fd, extra = 2, p2d, f"({p2d} больше)"
    else:
        fp = random.choice([1, 2])
        fd = p1d if fp == 1 else p2d
        extra = "(равно)"
    m = safe_send(cid, f"{EMO_MINE} Минное поле 5x5", parse_mode='HTML')
    if not m:
        return
    active_games[cid] = active_games.get(cid, {})
    active_games[cid][m.message_id] = {'p1_id': p1['user_id'], 'p2_id': p2['user_id'], 'board': board, 'mines': mines,
                                        'turn': fp, 'stake': stake, 'game_type': 'mines', 'finished': False,
                                        'processing': False, 'chat_id': cid, 'msg_id': m.message_id}
    safe_edit(cid, m.message_id, f"{EMO_MINE}\n{p1d} {EMO_VS} {p2d}\n{EMO_NOX} {stake:,} | {fd} {extra}",
              reply_markup=gen_mines_board(board, m.message_id), parse_mode='HTML')
    start_timer(cid, m.message_id, game_type='mines', timeout=60)


def gen_mines_board(board, mid):
    markup = types.InlineKeyboardMarkup(row_width=5)
    btns = []
    for i, c in enumerate(board):
        if c in ('⬜', '❓'):
            btns.append(btn('❓', callback_data=f"click_mines_{mid}_{i}", style='primary'))
        elif c == '✅':
            btns.append(btn(' ', callback_data="ignore", icon=ICO_SAFE))
        else:
            btns.append(btn(' ', callback_data="ignore", icon=ICO_MINE))
    for ch in [btns[i:i+5] for i in range(0, 25, 5)]:
        markup.add(*ch)
    markup.add(btn("СДАТЬСЯ", callback_data=f"surrender_mines_{mid}", style='danger', icon=ICO_SURRENDER))
    return markup


def gen_mines_final(mines):
    markup = types.InlineKeyboardMarkup(row_width=5)
    btns = [btn(' ', callback_data="ignore", icon=ICO_MINE if m else ICO_SAFE) for m in mines]
    for ch in [btns[i:i+5] for i in range(0, 25, 5)]:
        markup.add(*ch)
    return markup


@bot.callback_query_handler(func=lambda call: call.data.startswith("click_mines_"))
def click_mines(call):
    """Переписан: try/finally, safe_answer во всех ветках."""
    try:
        if check_banned(call.from_user.id, call.message.chat.id):
            return
        p = call.data.split("_")
        mid = int(p[2])
        idx = int(p[3])
        cid = call.message.chat.id
        uid = call.from_user.id
        if mid not in active_games.get(cid, {}):
            safe_answer(call.id, "❌ Игра не найдена", show_alert=True)
            return
        g = active_games[cid][mid]
        if g.get('finished', False):
            safe_answer(call.id, "❌ Игра завершена", show_alert=True)
            return
        if g.get('processing', False):
            safe_answer(call.id)
            return
        ct = g['p1_id'] if g['turn'] == 1 else g['p2_id']
        if uid != ct:
            safe_answer(call.id, "❌ Не твой ход!", show_alert=True)
            return
        if g['board'][idx] not in ('⬜', '❓'):
            safe_answer(call.id, "❌ Уже открыто", show_alert=True)
            return

        g['processing'] = True
        try:
            cancel_timer(cid, mid)
            if g['mines'][idx]:
                wid = g['p2_id'] if g['turn'] == 1 else g['p1_id']
                lid = ct
                g['finished'] = True
                wa = g['stake'] * 2
                update_balance(wid, wa)
                update_streak(wid, True, g['stake'])
                update_streak(lid, False, g['stake'])
                update_game_stats(wid, 'mines', True)
                update_game_stats(lid, 'mines', False)
                safe_edit(cid, mid,
                          f"{EMO_MINE} {get_user_display_by_id(lid)} на мине!\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,} {EMO_NOX}!",
                          reply_markup=gen_mines_final(g['mines']), parse_mode='HTML')
                del active_games[cid][mid]
                remove_player_from_game(wid)
                remove_player_from_game(lid)
                safe_answer(call.id, "💥!")
            else:
                g['board'][idx] = '✅'
                sc = [i for i, m in enumerate(g['mines']) if not m]
                op = [i for i, c in enumerate(g['board']) if c == '✅']
                if len(op) == len(sc):
                    update_balance(g['p1_id'], g['stake'])
                    update_balance(g['p2_id'], g['stake'])
                    g['finished'] = True
                    safe_edit(cid, mid, f"{EMO_HANDSHAKE} Ничья!", reply_markup=gen_mines_final(g['mines']), parse_mode='HTML')
                    del active_games[cid][mid]
                    remove_player_from_game(g['p1_id'])
                    remove_player_from_game(g['p2_id'])
                    safe_answer(call.id, "🤝")
                else:
                    g['turn'] = 2 if g['turn'] == 1 else 1
                    nid = g['p1_id'] if g['turn'] == 1 else g['p2_id']
                    safe_edit(cid, mid, f"{EMO_MINE}\n{EMO_NOX} {g['stake']:,} | {get_user_display_by_id(nid)}",
                              reply_markup=gen_mines_board(g['board'], mid), parse_mode='HTML')
                    start_timer(cid, mid, game_type='mines', timeout=60)
                    safe_answer(call.id, "✅")
        finally:
            try:
                g['processing'] = False
            except Exception:
                pass
    except Exception as e:
        print(f"[MINES] {e}")
        try:
            safe_answer(call.id, "❌ Ошибка", show_alert=True)
        except Exception:
            pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("surrender_mines_"))
def surrender_mines(call):
    safe_answer(call.id, "🏳️")
    p = call.data.split("_")
    mid = int(p[2])
    cid = call.message.chat.id
    uid = call.from_user.id
    if mid not in active_games.get(cid, {}):
        return
    g = active_games[cid][mid]
    if g.get('finished', False):
        return
    if uid == g['p1_id']:
        sid, wid = g['p1_id'], g['p2_id']
    elif uid == g['p2_id']:
        sid, wid = g['p2_id'], g['p1_id']
    else:
        return
    cancel_timer(cid, mid)
    g['finished'] = True
    wa = g['stake'] * 2
    update_balance(wid, wa)
    update_streak(wid, True, g['stake'])
    update_streak(sid, False, g['stake'])
    update_game_stats(wid, 'mines', True)
    update_game_stats(sid, 'mines', False)
    safe_edit(cid, mid, f"{EMO_SURRENDER} {get_user_display_by_id(sid)} СДАЛСЯ!\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,} {EMO_NOX}!",
              reply_markup=gen_mines_final(g['mines']), parse_mode='HTML')
    del active_games[cid][mid]
    remove_player_from_game(wid)
    remove_player_from_game(sid)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_mines_open_"))
def join_mines_open(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    hid = int(p[3])
    stake = int(p[4])
    mid = int(p[5])
    uid = call.from_user.id
    with invite_lock:
        if mid not in invites:
            return
        inv = invites[mid]
        if uid == hid or inv['game_type'] != 'mines':
            safe_answer(call.id, "❌", show_alert=True)
            return
        if check_player_in_game(uid):
            force_cleanup_player(uid)
        del invites[mid]
    h = get_or_create_user(hid, "", "")
    gu = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or gu['balance'] < stake:
        safe_answer(call.id, "❌ Мало!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    start_mines_match(call.message.chat.id, h, gu, stake)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_mines_"))
def join_mines(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    hid = int(p[2])
    tid = int(p[3])
    stake = int(p[4])
    mid = int(p[5])
    uid = call.from_user.id
    with invite_lock:
        if mid not in invites:
            return
        inv = invites[mid]
        if uid != tid or inv['game_type'] != 'mines':
            safe_answer(call.id, "Не твой!", show_alert=True)
            return
        if check_player_in_game(uid):
            force_cleanup_player(uid)
        del invites[mid]
    h = get_or_create_user(hid, "", "")
    gu = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or gu['balance'] < stake:
        safe_answer(call.id, "❌ Мало!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    start_mines_match(call.message.chat.id, h, gu, stake)


# ---------- УГАДАЙ ЧИСЛО ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith('число') and m.chat.type in ['group', 'supergroup'])
def cmd_number_game(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    match = re.match(r'^число\s+(\d+)\s+(\S+)$', message.text.strip().lower())
    if not match:
        safe_send(message.chat.id, f"{EMO_BULB} <code>число 100 [ставка]</code>", parse_mode='HTML')
        return
    mx = int(match.group(1))
    sa = match.group(2).strip()
    if mx < 2:
        safe_send(message.chat.id, f"{EMO_BULB} Диапазон > 1!", parse_mode='HTML')
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    if sa == 'вб':
        stake = user['balance']
    else:
        try:
            stake = int(sa)
        except ValueError:
            safe_send(message.chat.id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
    if stake < 1:
        safe_send(message.chat.id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
        return
    if user['balance'] < stake:
        safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
        return
    if check_player_in_game(message.from_user.id):
        force_cleanup_player(message.from_user.id)
    ud = get_user_display(user)
    if message.reply_to_message:
        tid = message.reply_to_message.from_user.id
        tgt = get_or_create_user(tid, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
        if tid == user['user_id']:
            safe_send(message.chat.id, f"{EMO_BULB} Себе!", parse_mode='HTML')
            return
        if tgt['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} Мало!", parse_mode='HTML')
            return
        if check_player_in_game(tid):
            safe_send(message.chat.id, f"{EMO_BULB} Соперник в игре!", parse_mode='HTML')
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_number_{message.from_user.id}_{tid}_{mx}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT),
                   btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_NUMBER} {ud} → {get_user_display(tgt)}!\n1-{mx}\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'number', 'stake': stake, 'chat_id': message.chat.id, 'max_num': mx}
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_number_open_{message.from_user.id}_{mx}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT),
                   btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_NUMBER} {ud} ищет соперника!\n1-{mx}\n{EMO_NOX} {stake:,}", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'number', 'stake': stake, 'chat_id': message.chat.id, 'max_num': mx}


def start_number_match(cid, p1, p2, mx, stake):
    add_player_to_game(p1['user_id'])
    add_player_to_game(p2['user_id'])
    secret = random.randint(1, mx)
    p1d, p2d = get_user_display(p1), get_user_display(p2)
    if p1['balance'] > p2['balance']:
        turn, td = p1['user_id'], p1d
    elif p2['balance'] > p1['balance']:
        turn, td = p2['user_id'], p2d
    else:
        turn = random.choice([p1['user_id'], p2['user_id']])
        td = p1d if turn == p1['user_id'] else p2d
    m = safe_send(cid, f"{EMO_NUMBER} Игра!\n{p1d} {EMO_VS} {p2d}\n1-{mx}\n{EMO_NOX} {stake:,}\nХодит: {td}", parse_mode='HTML')
    if not m:
        return
    active_games[cid] = active_games.get(cid, {})
    active_games[cid][m.message_id] = {'p1_id': p1['user_id'], 'p2_id': p2['user_id'], 'secret': secret, 'max_num': mx,
                                        'stake': stake, 'turn': turn, 'finished': False, 'game_type': 'number',
                                        'chat_id': cid, 'msg_id': m.message_id, 'attempts': [], 'timer_id': None}
    start_number_timer(cid, m.message_id)


def start_number_timer(cid, gmid):
    if cid not in active_games or gmid not in active_games[cid]:
        return
    g = active_games[cid][gmid]
    if g.get('finished', False):
        return
    if g.get('timer_id'):
        cancel_number_timer(cid, gmid)
    tid = f"number_{gmid}_{int(time.time()*1000)}"
    g['timer_id'] = tid
    if cid not in timer_flags:
        timer_flags[cid] = {}
    timer_flags[cid][gmid] = tid

    def tf():
        time.sleep(60)
        if cid not in timer_flags or gmid not in timer_flags[cid]:
            return
        if timer_flags[cid][gmid] != tid:
            return
        if cid not in active_games or gmid not in active_games[cid]:
            return
        gg = active_games[cid][gmid]
        if gg.get('finished', False):
            return
        cur = gg['turn']
        opp = gg['p1_id'] if cur == gg['p2_id'] else gg['p2_id']
        gg['finished'] = True
        wa = gg['stake'] * 2
        update_balance(opp, wa)
        update_streak(opp, True, gg['stake'])
        update_streak(cur, False, gg['stake'])
        update_game_stats(opp, 'number', True)
        update_game_stats(cur, 'number', False)
        at = ', '.join(map(str, gg['attempts'])) if gg['attempts'] else '-'
        safe_send(cid, f"{EMO_TIMER} {get_user_display_by_id(cur)} не сходил!\n{EMO_CROWN} {get_user_display_by_id(opp)} +{wa - gg['stake']:,} {EMO_NOX}!\n📝 {at}", parse_mode='HTML')
        del active_games[cid][gmid]
        if not active_games[cid]:
            del active_games[cid]
        remove_player_from_game(opp)
        remove_player_from_game(cur)
        if cid in timer_flags and gmid in timer_flags[cid]:
            del timer_flags[cid][gmid]

    t = threading.Thread(target=tf, daemon=True)
    if cid not in timer_threads:
        timer_threads[cid] = {}
    timer_threads[cid][gmid] = t
    t.start()


def cancel_number_timer(cid, gmid):
    if cid in timer_flags and gmid in timer_flags[cid]:
        timer_flags[cid][gmid] = None


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_number_open_"))
def join_number_open(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    hid = int(p[3])
    mx = int(p[4])
    stake = int(p[5])
    mid = int(p[6])
    uid = call.from_user.id
    with invite_lock:
        if mid not in invites:
            return
        inv = invites[mid]
        if uid == hid or inv['game_type'] != 'number':
            safe_answer(call.id, "❌", show_alert=True)
            return
        if check_player_in_game(uid):
            force_cleanup_player(uid)
        del invites[mid]
    h = get_or_create_user(hid, "", "")
    gu = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or gu['balance'] < stake:
        safe_answer(call.id, "❌ Мало!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    start_number_match(call.message.chat.id, h, gu, mx, stake)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_number_"))
def join_number(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    p = call.data.split("_")
    hid = int(p[2])
    tid = int(p[3])
    mx = int(p[4])
    stake = int(p[5])
    mid = int(p[6])
    uid = call.from_user.id
    with invite_lock:
        if mid not in invites:
            return
        inv = invites[mid]
        if uid != tid or inv['game_type'] != 'number':
            safe_answer(call.id, "Не твой!", show_alert=True)
            return
        if check_player_in_game(uid):
            force_cleanup_player(uid)
        del invites[mid]
    h = get_or_create_user(hid, "", "")
    gu = get_or_create_user(uid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or gu['balance'] < stake:
        safe_answer(call.id, "❌ Мало!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    start_number_match(call.message.chat.id, h, gu, mx, stake)


@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_invite_"))
def cancel_invite(call):
    mid = int(call.data.split("_")[2])
    uid = call.from_user.id
    with invite_lock:
        if mid not in invites:
            return
        inv = invites[mid]
        if uid != inv['host_id']:
            safe_answer(call.id, "❌ Только хост!", show_alert=True)
            return
        del invites[mid]
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    safe_answer(call.id, "✅ Отменена.")


# ---------- ТАЙМЕРЫ ----------

def start_timer(cid, mid, game_type='ttt', timeout=60):
    cancel_timer(cid, mid)
    if cid not in timer_flags:
        timer_flags[cid] = {}
    if cid not in timer_threads:
        timer_threads[cid] = {}
    tid = f"{mid}_{int(time.time() * 1000)}"
    timer_flags[cid][mid] = tid

    def tf():
        time.sleep(timeout)
        if cid not in timer_flags or mid not in timer_flags[cid]:
            return
        if timer_flags[cid][mid] != tid:
            return
        if game_type == 'eagle_choice':
            if cid in active_games:
                for gid, g in list(active_games[cid].items()):
                    if g.get('msg_id') == mid and g.get('game_type') == 'eagle' and not g.get('finished', False):
                        c_i, gs_i, st = g.get('chooser_id'), g.get('guesser_id'), g.get('stake')
                        if c_i and gs_i:
                            update_balance(c_i, st)
                            update_balance(gs_i, st)
                            remove_player_from_game(c_i)
                            remove_player_from_game(gs_i)
                        safe_edit(cid, mid, f"{EMO_TIMER} Время. Ставки возвращены.", parse_mode='HTML')
                        del active_games[cid][gid]
                        break
            invites.pop(mid, None)
            return
        if game_type == 'eagle_guess':
            if cid in active_games:
                for gid, g in list(active_games[cid].items()):
                    if g.get('msg_id') == mid and g.get('game_type') == 'eagle_guess' and not g.get('finished', False):
                        g['finished'] = True
                        c_i, gs_i, st = g['chooser_id'], g['guesser_id'], g['stake']
                        wa = st * 2
                        update_balance(c_i, wa)
                        update_streak(c_i, True, st)
                        update_streak(gs_i, False, st)
                        update_game_stats(c_i, 'eagle', True)
                        update_game_stats(gs_i, 'eagle', False)
                        safe_edit(cid, mid, f"{EMO_TIMER} {get_user_display_by_id(gs_i)} не угадал!\n{EMO_CROWN} {get_user_display_by_id(c_i)} +{wa - st:,} {EMO_NOX}!",
                                  parse_mode='HTML')
                        remove_player_from_game(c_i)
                        remove_player_from_game(gs_i)
                        del active_games[cid][gid]
                        break
            return
        if cid not in active_games or mid not in active_games[cid]:
            return
        g = active_games[cid][mid]
        if g.get('finished', False):
            return
        if game_type == 'rps':
            if g['p1_choice'] is None and g['p2_choice'] is None:
                update_balance(g['p1_id'], g['stake'])
                update_balance(g['p2_id'], g['stake'])
                safe_edit(cid, mid, f"{EMO_TIMER} Время!", parse_mode='HTML')
                del active_games[cid][mid]
                remove_player_from_game(g['p1_id'])
                remove_player_from_game(g['p2_id'])
            elif g['p1_choice'] is None or g['p2_choice'] is None:
                lid = g['p1_id'] if g['p1_choice'] is None else g['p2_id']
                wid = g['p2_id'] if g['p1_choice'] is None else g['p1_id']
                g['finished'] = True
                wa = g['stake'] * 2
                update_balance(wid, wa)
                update_streak(wid, True, g['stake'])
                update_streak(lid, False, g['stake'])
                update_game_stats(wid, 'rps', True)
                update_game_stats(lid, 'rps', False)
                safe_edit(cid, mid, f"{EMO_TIMER} {get_user_display_by_id(lid)} не сделал!\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,}!",
                          parse_mode='HTML')
                del active_games[cid][mid]
                remove_player_from_game(wid)
                remove_player_from_game(lid)
        elif game_type == 'ttt':
            cur, opp = (g['p1_id'], g['p2_id']) if g['turn'] == 'X' else (g['p2_id'], g['p1_id'])
            g['finished'] = True
            wa = g['stake'] * 2
            update_balance(opp, wa)
            update_streak(opp, True, g['stake'])
            update_streak(cur, False, g['stake'])
            update_game_stats(opp, 'ttt', True)
            update_game_stats(cur, 'ttt', False)
            safe_edit(cid, mid, f"{EMO_TIMER} {get_user_display_by_id(cur)} не сходил!\n{EMO_CROWN} {get_user_display_by_id(opp)} +{wa - g['stake']:,}!",
                      parse_mode='HTML')
            del active_games[cid][mid]
            remove_player_from_game(opp)
            remove_player_from_game(cur)
        elif game_type == 'mines':
            cur = g['p1_id'] if g['turn'] == 1 else g['p2_id']
            opp = g['p2_id'] if g['turn'] == 1 else g['p1_id']
            g['finished'] = True
            wa = g['stake'] * 2
            update_balance(opp, wa)
            update_streak(opp, True, g['stake'])
            update_streak(cur, False, g['stake'])
            update_game_stats(opp, 'mines', True)
            update_game_stats(cur, 'mines', False)
            safe_edit(cid, mid, f"{EMO_TIMER} {get_user_display_by_id(cur)} не сходил!\n{EMO_CROWN} {get_user_display_by_id(opp)} +{wa - g['stake']:,}!",
                      reply_markup=gen_mines_final(g['mines']), parse_mode='HTML')
            del active_games[cid][mid]
            remove_player_from_game(opp)
            remove_player_from_game(cur)
        elif game_type == 'roulette':
            cur = g['current_turn']
            opp = g['p1_id'] if cur == g['p2_id'] else g['p2_id']
            g['finished'] = True
            wa = g['stake'] * 2
            update_balance(opp, wa)
            update_streak(opp, True, g['stake'])
            update_streak(cur, False, g['stake'])
            update_game_stats(opp, 'roulette', True)
            update_game_stats(cur, 'roulette', False)
            safe_edit(cid, mid, f"{EMO_TIMER} {get_user_display_by_id(cur)} не выстрелил!\n{EMO_CROWN} {get_user_display_by_id(opp)} +{wa - g['stake']:,}!",
                      parse_mode='HTML')
            del active_games[cid][mid]
            remove_player_from_game(opp)
            remove_player_from_game(cur)
        if cid in timer_flags and mid in timer_flags[cid]:
            del timer_flags[cid][mid]

    t = threading.Thread(target=tf, daemon=True)
    timer_threads[cid][mid] = t
    t.start()


def cancel_timer(cid, mid):
    if cid in timer_flags and mid in timer_flags[cid]:
        timer_flags[cid][mid] = None


# ---------- МОДЕРАЦИЯ ----------

def is_moderator(user_id):
    conn = get_db_connection()
    cursor = db_cursor(conn)
    cursor.execute('SELECT 1 FROM moderators WHERE user_id = %s', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def get_target_user(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user, message.reply_to_message.from_user.id
    parts = message.text.strip().split()
    if len(parts) > 1:
        un = parts[1].replace('@', '')
        if un:
            try:
                u = bot.get_chat(f"@{un}")
                if u.type == 'private':
                    return u, u.id
            except Exception:
                pass
            try:
                uid = int(un)
                get_or_create_user(uid, "", "")
                return None, uid
            except Exception:
                pass
    return None, None


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'бан')
def cmd_ban_user(message):
    if not is_co_owner(message.from_user.id):
        return
    _, tid = get_target_user(message)
    if not tid:
        safe_send(message.chat.id, f"{EMO_CANCEL} Укажи юзера.", parse_mode='HTML')
        return
    if tid == OWNER_ID:
        safe_send(message.chat.id, f"{EMO_CANCEL} Владельца нельзя!", parse_mode='HTML')
        return
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('UPDATE users SET banned = 1 WHERE user_id = %s', (tid,))
        conn.commit()
        conn.close()
    safe_send(message.chat.id, f"{EMO_SAFE} {get_user_display_by_id(tid)} забанен.", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'разбан')
def cmd_unban_user(message):
    if not is_co_owner(message.from_user.id):
        return
    _, tid = get_target_user(message)
    if not tid:
        return
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('UPDATE users SET banned = 0 WHERE user_id = %s', (tid,))
        conn.commit()
        conn.close()
    safe_send(message.chat.id, f"{EMO_SAFE} {get_user_display_by_id(tid)} разбанен.", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'кик')
def cmd_kick_user(message):
    if not is_co_owner(message.from_user.id):
        safe_send(message.chat.id, f"{EMO_CANCEL} Нет прав!", parse_mode='HTML')
        return
    if message.chat.type not in ['group', 'supergroup']:
        safe_send(message.chat.id, f"{EMO_CANCEL} Только в группах!", parse_mode='HTML')
        return
    _, tid = get_target_user(message)
    if not tid or tid == OWNER_ID:
        safe_send(message.chat.id, f"{EMO_CANCEL} Ошибка.", parse_mode='HTML')
        return
    try:
        bot.ban_chat_member(message.chat.id, tid)
        bot.unban_chat_member(message.chat.id, tid)
        safe_send(message.chat.id, f"👢 {get_user_display_by_id(tid)} кикнут!", parse_mode='HTML')
    except Exception as e:
        safe_send(message.chat.id, f"{EMO_CANCEL} {e}", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith('пополнить'))
def cmd_owner_add_balance(message):
    if not is_co_owner(message.from_user.id):
        safe_send(message.chat.id, f"{EMO_CANCEL} Нет прав!", parse_mode='HTML')
        return
    parts = message.text.strip().lower().split()
    if len(parts) < 2:
        safe_send(message.chat.id, f"{EMO_CANCEL} <code>пополнить [сумма]</code>", parse_mode='HTML')
        return
    try:
        amount = int(parts[1])
    except Exception:
        safe_send(message.chat.id, f"{EMO_CANCEL} Число!", parse_mode='HTML')
        return
    if amount <= 0:
        return
    _, tid = get_target_user(message)
    if not tid:
        safe_send(message.chat.id, f"{EMO_CANCEL} Укажи юзера.", parse_mode='HTML')
        return
    update_balance(tid, amount)
    safe_send(message.chat.id, f"{EMO_CROWN} {get_user_display_by_id(tid)} +<b>{amount:,} {EMO_NOX}</b>!", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith('отжать'))
def cmd_withdraw_balance(message):
    if not is_co_owner(message.from_user.id):
        safe_send(message.chat.id, f"{EMO_CANCEL} Нет прав!", parse_mode='HTML')
        return
    parts = message.text.strip().lower().split()
    if len(parts) < 2:
        return
    try:
        amount = int(parts[1])
    except Exception:
        return
    if amount <= 0:
        return
    _, tid = get_target_user(message)
    if not tid or tid == OWNER_ID:
        return
    tu = get_or_create_user(tid, "", "")
    if tu['balance'] < amount:
        safe_send(message.chat.id, f"{EMO_CANCEL} Мало!", parse_mode='HTML')
        return
    update_balance(tid, -amount)
    update_balance(OWNER_ID, amount)
    tf = get_or_create_user(tid, "", "")
    safe_send(message.chat.id, f"{EMO_CROWN} Снял <b>{amount:,} {EMO_NOX}</b>!\n📉 Остаток: <b>{tf['balance']:,}</b>", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'модераторы')
def show_moderators(message):
    conn = get_db_connection()
    cursor = db_cursor(conn)
    cursor.execute("SELECT user_id, role FROM moderators ORDER BY CASE WHEN role='owner' THEN 0 ELSE 1 END")
    rows = cursor.fetchall()
    conn.close()
    co = get_co_owners()
    text = f"{EMO_MODS} <b>МОДЕРАТОРЫ</b>\n\n"
    for row in rows:
        u = get_or_create_user(row['user_id'], "", "")
        icon = EMO_CROWN if row['role'] == 'owner' else EMO_MODS
        role = "Владелец" if row['role'] == 'owner' else "Модератор"
        text += f"{icon} {role} — {get_user_display(u)}\n"
    if co:
        text += f"\n<b>Совладельцы:</b>\n"
        for c in co:
            text += f"• {get_user_display_by_id(c['user_id'])}\n"
    safe_send(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('мут'))
def mute_user(message):
    try:
        if not is_co_owner(message.from_user.id):
            safe_send(message.chat.id, f"{EMO_CANCEL} Нет прав!", parse_mode='HTML')
            return
        if message.chat.type not in ['group', 'supergroup']:
            return
        parts = message.text.split()
        if len(parts) < 2:
            safe_send(message.chat.id, f"{EMO_CANCEL} мут 1ч @user", parse_mode='HTML')
            return
        ts = parts[1].lower()
        tun = next((p[1:] for p in parts[2:] if p.startswith('@')), None)
        if not tun:
            if message.reply_to_message:
                tid = message.reply_to_message.from_user.id
            else:
                safe_send(message.chat.id, f"{EMO_CANCEL} Укажи юзера.", parse_mode='HTML')
                return
        else:
            tid = bot.get_chat_member(message.chat.id, f"@{tun}").user.id
        bcm = bot.get_chat_member(message.chat.id, get_bot_id())
        if not bcm.can_restrict_members:
            safe_send(message.chat.id, f"{EMO_CANCEL} Бот без прав.", parse_mode='HTML')
            return
        if tid == OWNER_ID:
            return
        if ts == 'навсегда':
            seconds = 315360000
        elif ts.endswith('м'):
            seconds = int(ts[:-1]) * 60
        elif ts.endswith('ч'):
            seconds = int(ts[:-1]) * 3600
        elif ts.endswith('д'):
            seconds = int(ts[:-1]) * 86400
        else:
            safe_send(message.chat.id, f"{EMO_CANCEL} Формат: 1ч, 30м, 1д", parse_mode='HTML')
            return
        until = datetime.datetime.now(timezone.utc) + datetime.timedelta(seconds=seconds)
        perms = types.ChatPermissions(can_send_messages=False, can_send_media=False, can_send_other_messages=False,
                                       can_add_web_page_previews=False, can_send_polls=False, can_change_info=False,
                                       can_invite_users=False, can_pin_messages=False)
        bot.restrict_chat_member(message.chat.id, tid, permissions=perms, until_date=until)
        safe_send(message.chat.id, f"{EMO_MUTE} {get_user_display_by_id(tid)} замучен на {ts}.", parse_mode='HTML')
    except Exception as e:
        safe_send(message.chat.id, f"{EMO_CANCEL} {e}", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'размут')
def unmute_user(message):
    try:
        if not is_co_owner(message.from_user.id):
            return
        if message.chat.type not in ['group', 'supergroup']:
            return
        tun = next((p[1:] for p in message.text.split()[1:] if p.startswith('@')), None)
        if not tun:
            if message.reply_to_message:
                tid = message.reply_to_message.from_user.id
            else:
                safe_send(message.chat.id, f"{EMO_CANCEL} Укажи.", parse_mode='HTML')
                return
        else:
            tid = bot.get_chat_member(message.chat.id, f"@{tun}").user.id
        perms = types.ChatPermissions(can_send_messages=True, can_send_media=True, can_send_other_messages=True,
                                       can_add_web_page_previews=True, can_send_polls=True, can_change_info=True,
                                       can_invite_users=True, can_pin_messages=True)
        bot.restrict_chat_member(message.chat.id, tid, permissions=perms, until_date=None)
        safe_send(message.chat.id, f"{EMO_SAFE} {get_user_display_by_id(tid)} размучен.", parse_mode='HTML')
    except Exception as e:
        safe_send(message.chat.id, f"{EMO_CANCEL} {e}", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'удалить')
def cmd_delete_message(message):
    if not is_co_owner(message.from_user.id):
        return
    if not message.reply_to_message:
        return
    try:
        bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass


@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('повысить'))
def cmd_promote_moderator(message):
    if message.from_user.id != OWNER_ID:
        return
    _, tid = get_target_user(message)
    if not tid or tid == OWNER_ID or is_moderator(tid):
        return
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('INSERT INTO moderators (user_id, role, added_by) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO NOTHING',
                       (tid, 'moderator', OWNER_ID))
        conn.commit()
        conn.close()
    safe_send(message.chat.id, f"{EMO_SAFE} {get_user_display_by_id(tid)} теперь модератор!", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('снять'))
def cmd_demote_moderator(message):
    if message.from_user.id != OWNER_ID:
        return
    _, tid = get_target_user(message)
    if not tid or tid == OWNER_ID:
        return
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute("DELETE FROM moderators WHERE user_id = %s AND role != 'owner'", (tid,))
        conn.commit()
        conn.close()
    safe_send(message.chat.id, f"{EMO_SAFE} {get_user_display_by_id(tid)} больше не модератор.", parse_mode='HTML')


# ---------- АДМИН-ПАНЕЛЬ ----------

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel" and is_co_owner(call.from_user.id))
def admin_panel(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(btn("Накрутить себе", callback_data="adm_refill_input", style='success', icon=ICO_GOLD_BTN))
    markup.add(btn("Обнулить баланс", callback_data="adm_reset_balance", style='danger', icon=ICO_CANCEL))
    markup.add(btn("Рассылка", callback_data="adm_mailing", style='primary', icon=ICO_CHANNEL))
    markup.add(btn("Пополнить юзера", callback_data="adm_user_add", style='success', icon=ICO_DONATE))
    markup.add(btn("Создать промо", callback_data="adm_gen_promo", style='primary', icon=ICO_PROMO))
    markup.add(btn("Список юзеров", callback_data="adm_users_list", style='primary', icon=ICO_PROFILE))
    markup.add(btn("История промо", callback_data="adm_promo_history", style='success', icon=ICO_PROMO))
    markup.add(btn("Подписка", callback_data="adm_subscriptions", style='success', icon=ICO_CHANNEL))
    markup.add(btn("Чаты (подписка)", callback_data="adm_subscription_management", style='primary', icon=ICO_CHAT))
    if call.from_user.id == OWNER_ID:
        markup.add(btn("👑 Совладельцы", callback_data="adm_co_owners", style='success', icon=ICO_ADMIN))
        markup.add(btn("Перезагрузить", callback_data="adm_restart", style='danger', icon=ICO_TIMER))
    markup.add(btn("Назад", callback_data="back_to_menu", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, f"{EMO_ADMIN} <b>Админ-панель</b>",
              reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "adm_co_owners" and call.from_user.id == OWNER_ID)
def adm_co_owners(call):
    co = get_co_owners()
    text = f"{EMO_ADMIN} <b>СОВЛАДЕЛЬЦЫ</b>\n\n"
    if co:
        for c in co:
            text += f"• {get_user_display_by_id(c['user_id'])}\n"
    else:
        text += "<i>Пусто</i>\n"
    text += "\nСовладельцы имеют доступ к командам: отжать, пополнить, мут, бан, удалить и т.д."
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(btn("➕ Добавить", callback_data="adm_co_add", style='success', icon=ICO_SAFE))
    for c in co:
        markup.add(btn(f"🗑 Убрать {get_user_display_by_id(c['user_id'])}",
                       callback_data=f"adm_co_del_{c['user_id']}", style='danger', icon=ICO_CANCEL))
    markup.add(btn("Назад", callback_data="admin_panel", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "adm_co_add" and call.from_user.id == OWNER_ID)
def adm_co_add(call):
    msg = safe_send(call.message.chat.id,
                    f"{EMO_INPUT} Отправь <b>ID</b> или <b>@username</b> нового совладельца:", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_co_add)
    safe_answer(call.id)


def process_co_add(message):
    if message.from_user.id != OWNER_ID:
        return
    txt = message.text.strip()
    uid = None
    if txt.startswith('@'):
        try:
            u = bot.get_chat(txt)
            uid = u.id
        except Exception:
            safe_send(message.chat.id, f"{EMO_CANCEL} Не найден @.", parse_mode='HTML')
            return
    else:
        try:
            uid = int(txt)
        except Exception:
            safe_send(message.chat.id, f"{EMO_CANCEL} Нужен ID или @username.", parse_mode='HTML')
            return
    if uid == OWNER_ID:
        safe_send(message.chat.id, f"{EMO_CANCEL} Ты и так владелец!", parse_mode='HTML')
        return
    get_or_create_user(uid, "", "")
    add_co_owner(uid, OWNER_ID)
    safe_send(message.chat.id, f"{EMO_SAFE} {get_user_display_by_id(uid)} теперь совладелец!", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_co_del_") and call.from_user.id == OWNER_ID)
def adm_co_del(call):
    uid = int(call.data.split("_")[3])
    remove_co_owner(uid)
    safe_answer(call.id, "✅ Убран", show_alert=True)
    adm_co_owners(call)


@bot.callback_query_handler(func=lambda call: call.data == "adm_restart" and call.from_user.id == OWNER_ID)
def adm_restart(call):
    safe_answer(call.id, "🔄")
    safe_edit(call.message.chat.id, call.message.message_id, f"{EMO_TIMER} Перезагрузка...", parse_mode='HTML')
    time.sleep(1)
    try:
        subprocess.Popen([sys.executable] + sys.argv, stdout=open('bot.log', 'a'), stderr=subprocess.STDOUT, start_new_session=True)
    except Exception:
        pass
    os._exit(0)


@bot.callback_query_handler(func=lambda call: call.data == "adm_refill_input" and is_co_owner(call.from_user.id))
def adm_refill_input(call):
    msg = safe_send(call.message.chat.id, f"{EMO_NOX} Сумма:", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_admin_refill)
    safe_answer(call.id)


def process_admin_refill(message):
    if not is_co_owner(message.from_user.id):
        return
    try:
        a = int(message.text.strip())
        if a <= 0:
            return
        update_balance(message.from_user.id, a)
        u = get_or_create_user(message.from_user.id, "", "")
        safe_send(message.chat.id, f"{EMO_SAFE} +{a:,}! Баланс: <code>{u['balance']:,}</code>", parse_mode='HTML')
    except Exception:
        safe_send(message.chat.id, f"{EMO_CANCEL} Число!", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "adm_reset_balance" and is_co_owner(call.from_user.id))
def adm_reset_balance(call):
    set_balance(call.from_user.id, 0)
    safe_send(call.message.chat.id, f"{EMO_CANCEL} Обнулён!", parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "adm_mailing" and is_co_owner(call.from_user.id))
def adm_mailing(call):
    msg = safe_send(call.message.chat.id, f"{EMO_CHANNEL} Текст:", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_mailing)
    safe_answer(call.id)


def process_mailing(message):
    if not is_co_owner(message.from_user.id):
        return
    t = message.text
    if not t:
        return
    us = get_all_users()
    s, f = 0, 0
    for r in us:
        if r['user_id'] == OWNER_ID:
            continue
        try:
            bot.send_message(r['user_id'], t, parse_mode='HTML')
            s += 1
            time.sleep(0.05)
        except Exception:
            f += 1
    ch = get_all_chats()
    sc, cf = 0, 0
    for r in ch:
        try:
            bot.send_message(r['chat_id'], t, parse_mode='HTML')
            sc += 1
            time.sleep(0.05)
        except Exception:
            cf += 1
    safe_send(message.chat.id, f"📢 Готово\n✅ ЛС: {s} | ❌ {f}\n✅ Чаты: {sc} | ❌ {cf}", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "adm_user_add" and is_co_owner(call.from_user.id))
def adm_user_add(call):
    msg = safe_send(call.message.chat.id, f"{EMO_NOX} ID сумма:", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_admin_add_user)
    safe_answer(call.id)


def process_admin_add_user(message):
    if not is_co_owner(message.from_user.id):
        return
    try:
        p = message.text.strip().split()
        uid = int(p[0])
        a = int(p[1])
        if a <= 0:
            return
        get_or_create_user(uid, "", "")
        update_balance(uid, a)
        t = get_or_create_user(uid, "", "")
        safe_send(message.chat.id, f"{EMO_SAFE} {get_user_display(t)} +{a:,}! Баланс: <code>{t['balance']:,}</code>", parse_mode='HTML')
    except Exception:
        safe_send(message.chat.id, f"{EMO_CANCEL} Формат: ID сумма", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "adm_gen_promo" and is_co_owner(call.from_user.id))
def adm_gen_promo(call):
    msg = safe_send(call.message.chat.id, "Введи: <b>код</b> <b>активаций</b> <b>сумма</b>", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_promo_create)
    safe_answer(call.id)


def process_promo_create(message):
    if not is_co_owner(message.from_user.id):
        return
    try:
        parts = message.text.strip().split()
        if len(parts) < 3:
            raise ValueError("Мало")
        mx = int(parts[-2])
        rw = int(parts[-1])
        code = " ".join(parts[:-2])
        if not code or mx <= 0 or rw <= 0:
            raise ValueError("Пусто")
        with db_lock:
            conn = get_db_connection()
            cur = db_cursor(conn)
            cur.execute('''INSERT INTO promos (code, reward, max_uses, current_uses) VALUES (%s, %s, %s, 0)
                ON CONFLICT (code) DO UPDATE SET reward = EXCLUDED.reward, max_uses = EXCLUDED.max_uses, current_uses = 0''',
                (code, rw, mx))
            conn.commit()
            conn.close()
        safe_send(message.chat.id, f"{EMO_SAFE} Промо: <code>{code}</code>\n{EMO_NOX} {rw:,}\n👥 {mx}", parse_mode='HTML')
    except Exception:
        safe_send(message.chat.id, "❌ Формат: <b>код</b> <b>активаций</b> <b>сумма</b>", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "adm_users_list" and is_co_owner(call.from_user.id))
def adm_users_list(call):
    rows = get_all_users()
    if not rows:
        safe_send(call.message.chat.id, f"{EMO_CANCEL} Пусто.", parse_mode='HTML')
        safe_answer(call.id)
        return
    user_list_cache[call.from_user.id] = rows
    show_user_page(call.message.chat.id, call.from_user.id, 0, call.message.message_id)
    safe_answer(call.id)


def show_user_page(cid, uid, page, mid=None):
    rows = user_list_cache.get(uid, [])
    if not rows:
        return
    total = len(rows)
    pp = 50
    pages = (total - 1) // pp + 1
    page = max(0, min(page, pages - 1))
    st = page * pp
    en = min(st + pp, total)
    t = f"👥 <b>Юзеры</b> ({total}, стр. {page+1}/{pages})\n"
    for i in range(st, en):
        row = rows[i]
        t += f"{i+1}. {get_user_display(row)} — <code>{row['balance']:,}</code>\n"
    markup = types.InlineKeyboardMarkup(row_width=2)
    if page > 0:
        markup.add(btn("◀️", callback_data=f"user_page_{page-1}", style='primary', icon=ICO_BACK))
    if page < pages - 1:
        markup.add(btn("▶️", callback_data=f"user_page_{page+1}", style='primary'))
    markup.add(btn("В админку", callback_data="admin_panel", style='danger', icon=ICO_BACK))
    if mid:
        safe_edit(cid, mid, t, parse_mode='HTML', reply_markup=markup)
    else:
        safe_send(cid, t, parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("user_page_") and is_co_owner(call.from_user.id))
def user_page_callback(call):
    page = int(call.data.split("_")[2])
    show_user_page(call.message.chat.id, call.from_user.id, page, call.message.message_id)
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: (call.data == "adm_promo_history" or call.data.startswith("adm_promo_page_")) and is_co_owner(call.from_user.id))
def adm_promo_history(call):
    safe_answer(call.id)
    page = 1
    if call.data.startswith("adm_promo_page_"):
        page = int(call.data.split("_")[3])
    try:
        with db_lock:
            conn = get_db_connection()
            cursor = db_cursor(conn)
            cursor.execute('SELECT code, reward, max_uses, current_uses FROM promos ORDER BY code DESC')
            all_promos = cursor.fetchall()
            if not all_promos:
                safe_send(call.message.chat.id, f"{EMO_CANCEL} Пусто.", parse_mode='HTML')
                conn.close()
                return
            tp = (len(all_promos) + PROMOS_PER_PAGE - 1) // PROMOS_PER_PAGE
            page = max(1, min(page, tp))
            si = (page - 1) * PROMOS_PER_PAGE
            pp = all_promos[si:si + PROMOS_PER_PAGE]
            text = f"📋 <b>ИСТОРИЯ (Стр. {page}/{tp})</b>\n"
            for p in pp:
                code = p['code']
                text += f"\n<b>Код:</b> <code>{code}</code>\n{EMO_NOX} {p['reward']:,} | {p['current_uses']}/{p['max_uses']}\n"
                cursor.execute('SELECT u.username, u.first_name, ph.activated_at FROM promo_history ph JOIN users u ON ph.user_id = u.user_id WHERE ph.code = %s ORDER BY ph.activated_at DESC', (code,))
                users = cursor.fetchall()
                if users:
                    ul = []
                    for u in users:
                        nm = f"@{u['username']}" if u['username'] else u['first_name']
                        try:
                            dt = u['activated_at'].strftime('%Y-%m-%d %H:%M') if u['activated_at'] else ''
                        except Exception:
                            dt = str(u['activated_at'])[:16] if u['activated_at'] else ''
                        ul.append(f"{nm} ({dt})")
                    text += "👤 " + ", ".join(ul) + "\n"
                else:
                    text += "👤 никто\n"
            conn.close()
        markup = types.InlineKeyboardMarkup()
        nav = []
        if page > 1:
            nav.append(btn("◀️", callback_data=f"adm_promo_page_{page-1}", style='primary', icon=ICO_BACK))
        if page < tp:
            nav.append(btn("▶️", callback_data=f"adm_promo_page_{page+1}", style='primary'))
        if nav:
            markup.row(*nav)
        markup.add(btn("В админку", callback_data="admin_panel", style='danger', icon=ICO_BACK))
        if call.data.startswith("adm_promo_page_"):
            safe_edit(call.message.chat.id, call.message.message_id, text, parse_mode='HTML', reply_markup=markup)
        else:
            safe_send(call.message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        safe_send(call.message.chat.id, f"Ошибка: <code>{e}</code>", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "adm_subscriptions" and is_co_owner(call.from_user.id))
def adm_subscriptions(call):
    subs = get_required_subscriptions()
    text = f"{EMO_CHANNEL} <b>Обязательные подписки</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for sub in subs:
        text += f"• {sub['title']} — {sub['link']}\n"
        markup.add(btn(f"🗑 Удалить {sub['title']}", callback_data=f"del_sub_{sub['id']}", style='danger', icon=ICO_CANCEL))
    markup.add(btn("➕ Добавить", callback_data="add_sub_start", style='success', icon=ICO_SAFE))
    markup.add(btn("Назад", callback_data="admin_panel", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "add_sub_start" and is_co_owner(call.from_user.id))
def add_sub_start(call):
    msg = safe_send(call.message.chat.id, f"{EMO_INPUT} Введи: <b>ID</b> <b>тип</b> <b>ссылка</b> <b>название</b>", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_add_sub)
    safe_answer(call.id)


def process_add_sub(message):
    if not is_co_owner(message.from_user.id):
        return
    try:
        parts = message.text.strip().split(maxsplit=3)
        cid = int(parts[0])
        t = parts[1]
        l = parts[2]
        tt = parts[3]
        add_required_subscription(cid, t, l, tt)
        safe_send(message.chat.id, f"{EMO_SAFE} {tt} добавлена!", parse_mode='HTML')
    except Exception as e:
        safe_send(message.chat.id, f"{EMO_CANCEL} {e}", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data.startswith("del_sub_") and is_co_owner(call.from_user.id))
def del_sub(call):
    sid = int(call.data.split("_")[2])
    try:
        remove_required_subscription(sid)
        safe_answer(call.id, "✅")
    except Exception as e:
        safe_answer(call.id, f"❌ {e}", show_alert=True)
    adm_subscriptions(call)


@bot.callback_query_handler(func=lambda call: call.data == "adm_subscription_management" and is_co_owner(call.from_user.id))
def adm_subscription_management(call):
    bid = get_bot_id()
    chats = get_all_chats()
    admin_chats = []
    for row in chats:
        try:
            m = bot.get_chat_member(row['chat_id'], bid)
            if m.status in ('administrator', 'creator'):
                admin_chats.append(row)
            else:
                with db_lock:
                    conn = get_db_connection()
                    cursor = db_cursor(conn)
                    cursor.execute('DELETE FROM chats WHERE chat_id = %s', (row['chat_id'],))
                    conn.commit()
                    conn.close()
        except Exception:
            with db_lock:
                conn = get_db_connection()
                cursor = db_cursor(conn)
                cursor.execute('DELETE FROM chats WHERE chat_id = %s', (row['chat_id'],))
                conn.commit()
                conn.close()
    text = f"{EMO_CHAT} <b>Чаты где бот админ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    if admin_chats:
        for row in admin_chats:
            st = "✅" if row['sub_required'] else "❌"
            ns = 0 if row['sub_required'] else 1
            title = row['chat_title'] or row['chat_id']
            link = get_chat_link(row['chat_id'])
            if link:
                markup.add(btn(f"🔗 {title}", url=link, style='primary', icon=ICO_CHAT))
            else:
                text += f"• {title} (без ссылки)\n"
            markup.add(btn(f"{st} Подписка: {title}", callback_data=f"toggle_subreq_{row['chat_id']}_{ns}", style='primary', icon=ICO_CHAT))
            markup.add(btn(f"🗑 Удалить {title}", callback_data=f"del_chat_{row['chat_id']}", style='danger', icon=ICO_CANCEL))
    else:
        text += "Нет.\n"
    markup.add(btn("Назад", callback_data="admin_panel", style='danger', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("del_chat_") and is_co_owner(call.from_user.id))
def del_chat(call):
    cid = int(call.data.split("_")[2])
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('DELETE FROM chats WHERE chat_id = %s', (cid,))
        conn.commit()
        conn.close()
    safe_answer(call.id, "✅")
    adm_subscription_management(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_subreq_") and is_co_owner(call.from_user.id))
def toggle_subreq(call):
    p = call.data.split("_")
    cid = int(p[2])
    ns = int(p[3])
    with db_lock:
        conn = get_db_connection()
        cursor = db_cursor(conn)
        cursor.execute('UPDATE chats SET sub_required = %s WHERE chat_id = %s', (ns, cid))
        conn.commit()
        conn.close()
    safe_answer(call.id, "✅")
    adm_subscription_management(call)


@bot.callback_query_handler(func=lambda call: call.data == "ignore")
def ignore_callback(call):
    safe_answer(call.id)


# ---------- NUMBER ACTIVE FILTER ----------

def _has_active_number_game(cid):
    if cid not in active_games:
        return False
    for g in active_games[cid].values():
        if g.get('game_type') == 'number' and not g.get('finished', False):
            return True
    return False


@bot.message_handler(content_types=['text'],
                     func=lambda m: m.chat.type in ['group', 'supergroup'] and _has_active_number_game(m.chat.id))
def handle_number_game_messages(message):
    if not message.text:
        return
    text = message.text.strip()
    lw = text.lower()
    if lw != 'сдаюсь' and not lw.isdigit():
        return
    cid = message.chat.id
    uid = message.from_user.id
    gfound = False
    gmid = None
    g = None
    if cid in active_games:
        for mid, game in active_games[cid].items():
            if game.get('game_type') == 'number' and not game.get('finished', False):
                gfound = True
                gmid = mid
                g = game
                break
    if not gfound:
        return
    if uid != g['p1_id'] and uid != g['p2_id']:
        return
    if uid != g['turn']:
        safe_send(cid, f"{EMO_BULB} Не твой ход!", parse_mode='HTML')
        return
    if lw == 'сдаюсь':
        g['finished'] = True
        cancel_number_timer(cid, gmid)
        sid = uid
        wid = g['p1_id'] if uid == g['p2_id'] else g['p2_id']
        wa = g['stake'] * 2
        update_balance(wid, wa)
        update_streak(wid, True, g['stake'])
        update_streak(sid, False, g['stake'])
        update_game_stats(wid, 'number', True)
        update_game_stats(sid, 'number', False)
        safe_send(cid, f"{EMO_SURRENDER} {get_user_display_by_id(sid)} СДАЛСЯ!\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,} {EMO_NOX}!",
                  parse_mode='HTML')
        del active_games[cid][gmid]
        if not active_games[cid]:
            del active_games[cid]
        remove_player_from_game(wid)
        remove_player_from_game(sid)
        return
    try:
        guess = int(text)
    except Exception:
        return
    if guess < 1 or guess > g['max_num']:
        safe_send(cid, f"{EMO_BULB} Число 1-{g['max_num']}!", parse_mode='HTML')
        return
    cancel_number_timer(cid, gmid)
    g['attempts'].append(guess)
    if guess == g['secret']:
        g['finished'] = True
        wid = uid
        lid = g['p1_id'] if uid == g['p2_id'] else g['p2_id']
        wa = g['stake'] * 2
        update_balance(wid, wa)
        update_streak(wid, True, g['stake'])
        update_streak(lid, False, g['stake'])
        update_game_stats(wid, 'number', True)
        update_game_stats(lid, 'number', False)
        at = ', '.join(map(str, g['attempts']))
        safe_send(cid, f"🎉 {get_user_display_by_id(wid)} угадал {g['secret']}!\n📝 {at}\n{EMO_CROWN} +{wa - g['stake']:,} {EMO_NOX}!",
                  parse_mode='HTML')
        del active_games[cid][gmid]
        if not active_games[cid]:
            del active_games[cid]
        remove_player_from_game(wid)
        remove_player_from_game(lid)
    else:
        g['turn'] = g['p1_id'] if g['turn'] == g['p2_id'] else g['p2_id']
        nd = get_user_display_by_id(g['turn'])
        at = ', '.join(map(str, g['attempts']))
        safe_send(cid, f"{EMO_BULB} Не угадал. Ходит: {nd}\n{EMO_TIMER} 60 сек!\n📝 {at}", parse_mode='HTML')
        start_number_timer(cid, gmid)


# ---------- BIO BONUS HOOK (с throttle) ----------

@bot.message_handler(content_types=['text'], func=lambda m: m.chat.type in ['group', 'supergroup'] and
                                                                not (m.text or '').startswith('/'))
def bio_bonus_hook(message):
    try:
        if not message.from_user:
            return
        if message.from_user.is_bot:
            return
        txt_lower = (message.text or '').strip().lower()
        if txt_lower in ('б', 'бонус', 'профиль'):
            return
        uid = message.from_user.id
        now = time.time()
        if uid in _vip_check_cache and now - _vip_check_cache[uid] < VIP_CHECK_INTERVAL:
            return
        _vip_check_cache[uid] = now
        activate_vip(uid, message.chat.id, message)
    except Exception as e:
        print(f"[BIO HOOK ERR] {e}")


# ---------- VIP REMINDER (каждые 15 часов) ----------

def vip_reminder_loop():
    # первая отправка через 15 часов после старта
    while True:
        time.sleep(15 * 3600)
        try:
            bu = bot.get_me().username
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(btn("Подключить бесплатно VIP статус",
                           url=f"https://t.me/{bu}?start=vip",
                           style='success', icon=ICO_VIP))
            text = (f"{EMO_VIP} <b>НАПОМИНАНИЕ О VIP-СТАТУСЕ</b> {EMO_VIP}\n\n"
                    f"{EMO_NOX} Получи <b>5000</b> ноксов — если ссылка только в нико или только в Bio\n"
                    f"{EMO_NOX} Получи <b>7500</b> ноксов — если ссылка и в нико, и в Bio\n"
                    f"{EMO_VIP} + VIP-значок рядом с ником\n"
                    f"{EMO_NOX} И столько же каждый день в 00:00 МСК\n\n"
                    f"{EMO_BULB} Нажми на кнопку ниже, чтобы подключить:")
            for row in get_all_chats():
                try:
                    safe_send(row['chat_id'], text, parse_mode='HTML', reply_markup=markup)
                    time.sleep(0.1)
                except Exception:
                    pass
        except Exception as e:
            print(f"[VIP REMINDER ERR] {e}")


# ---------- HTTP ----------

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'NoxHub bot is running')

    def log_message(self, format, *args):
        pass


def start_http_server():
    port = int(os.environ.get('PORT', '10000'))
    try:
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        print(f"[HTTP] Порт {port}")
    except Exception as e:
        print(f"[HTTP ERR] {e}")


if __name__ == '__main__':
    if not DATABASE_URL:
        print("❌ DATABASE_URL не задан!")
        sys.exit(1)
    start_http_server()
    init_db()
    # Поток напоминания о VIP (каждые 15 часов)
    threading.Thread(target=vip_reminder_loop, daemon=True).start()
    print("🤖 NoxHub запущен!")
    bot.infinity_polling(allowed_updates=['message', 'callback_query', 'chat_member', 'my_chat_member', 'left_chat_member'])
