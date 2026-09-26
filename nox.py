import telebot
from telebot import types
import psycopg2
from psycopg2.extras import RealDictCursor
import random, re, threading, time, datetime, sys, subprocess, os
from datetime import timedelta, timezone

API_TOKEN = '8823737566:AAHDmpJlY5xAFxLlO4QeO2GddIpg3Ibz0Hk'
OWNER_ID = 5825717381
OWNER_USERNAME = 'NorikAmiri'
BOT_PHOTO_URL = 'https://ibb.co/jSGN6J2'
CHAT_LINK = 'https://t.me/Nox_chatik'

# ==== БД ====
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgres://avnadmin:AVNS_JUchdhYFhyD2305NNnC@pg-3293e11c-gretahacatran-7546.e.aivencloud.com:28434/defaultdb?sslmode=require"
)

bot = telebot.TeleBot(API_TOKEN)

active_games = {}
timer_flags = {}
timer_threads = {}
invites = {}
db_lock = threading.Lock()
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
CLAN_CREATE_COST = 100000
CLAN_SLOT_COST = 5000
CLAN_BASE_SLOTS = 5
CLAN_EMOJI_PER_PAGE = 20

QUICK_BONUS_INTERVAL = 10 * 60
QUICK_BONUS_AMOUNT = 500

BOT_ID_CACHE = {'id': None}


def get_bot_id():
    if BOT_ID_CACHE['id'] is None:
        try:
            BOT_ID_CACHE['id'] = bot.get_me().id
        except Exception:
            return None
    return BOT_ID_CACHE['id']


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
EMO_ORANGE = '<tg-emoji emoji-id="5792092620784146419">🍊</tg-emoji>'
EMO_DIAMOND = '<tg-emoji emoji-id="5791633806607782442">💎</tg-emoji>'
EMO_LEMON = '<tg-emoji emoji-id="5791734858598323525">🍋</tg-emoji>'
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
EMO_CLAN = '<tg-emoji emoji-id="5285423837205260312">🎟</tg-emoji>'
EMO_CLAN_HEADER = '<tg-emoji emoji-id="5224575413253274698">🏰</tg-emoji>'

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
ICO_CLAN_HEADER = '5224575413253274698'

SLOT_EMOJI_MAP = {'🍒': EMO_CHERRY, '🍋': EMO_LEMON, '🍊': EMO_ORANGE, '💎': EMO_DIAMOND}

TG_EMOJI_RE = re.compile(r'<tg-emoji emoji-id="[^"]*">([^<]*)</tg-emoji>')


def strip_tg_emoji(text):
    if not text:
        return text
    return TG_EMOJI_RE.sub(r'\1', text)


def clean_markup(markup):
    if not markup:
        return None
    try:
        new_kb = types.InlineKeyboardMarkup(row_width=markup.row_width)
        for row in markup.keyboard:
            new_row = []
            for b in row:
                cb = getattr(b, 'callback_data', None)
                url = getattr(b, 'url', None)
                new_row.append(types.InlineKeyboardButton(text=b.text, callback_data=cb, url=url))
            new_kb.row(*new_row)
        return new_kb
    except Exception:
        return None


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
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 429:
            retry_after = 3
            try:
                if hasattr(e, 'result_json') and e.result_json:
                    retry_after = e.result_json.get('parameters', {}).get('retry_after', 3)
            except Exception:
                pass
            print(f"[429] chat={chat_id} wait {retry_after}s")
            time.sleep(retry_after + 1)
            try:
                return bot.send_message(chat_id, text, **kwargs)
            except Exception:
                return None
        elif e.error_code == 400 and 'DOCUMENT_INVALID' in str(e):
            print(f"[DOC_INVALID] chat={chat_id} -> clean text+markup")
            clean_text = strip_tg_emoji(text)
            clean_kb = clean_markup(kwargs.get('reply_markup'))
            new_kwargs = dict(kwargs)
            if clean_kb is not None:
                new_kwargs['reply_markup'] = clean_kb
            else:
                new_kwargs.pop('reply_markup', None)
            try:
                return bot.send_message(chat_id, clean_text, **new_kwargs)
            except Exception as ee:
                print(f"[DOC_INVALID retry fail] {ee}")
                return None
        else:
            print(f"[send ERR] chat={chat_id} code={e.error_code}: {e}")
            return None
    except Exception as e:
        print(f"[send EXC] {type(e).__name__}: {e}")
        return None


def safe_edit(chat_id, message_id, text, **kwargs):
    try:
        return bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, **kwargs)
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 429:
            retry_after = 3
            try:
                if hasattr(e, 'result_json') and e.result_json:
                    retry_after = e.result_json.get('parameters', {}).get('retry_after', 3)
            except Exception:
                pass
            print(f"[429 edit] wait {retry_after}s")
            time.sleep(retry_after + 1)
            try:
                return bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, **kwargs)
            except Exception:
                return None
        elif e.error_code == 400 and 'DOCUMENT_INVALID' in str(e):
            print(f"[DOC_INVALID edit] clean text+markup")
            clean_text = strip_tg_emoji(text)
            clean_kb = clean_markup(kwargs.get('reply_markup'))
            new_kwargs = dict(kwargs)
            if clean_kb is not None:
                new_kwargs['reply_markup'] = clean_kb
            else:
                new_kwargs.pop('reply_markup', None)
            try:
                return bot.edit_message_text(clean_text, chat_id=chat_id, message_id=message_id, **new_kwargs)
            except Exception:
                return None
        elif e.error_code == 400 and ('message is not modified' in str(e) or 'no text in the message' in str(e)):
            try:
                return bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=message_id, **kwargs)
            except Exception:
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception:
                    pass
                return safe_send(chat_id, text, **kwargs)
        else:
            print(f"[edit ERR] code={e.error_code}: {e}")
            return None
    except Exception as e:
        print(f"[edit EXC] {type(e).__name__}: {e}")
        return None


def safe_answer(call_id, text=None, show_alert=False):
    try:
        if text:
            bot.answer_callback_query(call_id, text, show_alert=show_alert)
        else:
            bot.answer_callback_query(call_id)
    except Exception:
        pass


# ============================================================
#                     POSTGRESQL СЛОЙ
# ============================================================

def get_db_connection():
    """Подключение к PostgreSQL (Aiven) с RealDictCursor."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def _get_columns(cursor, table):
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s
    """, (table,))
    return [r['column_name'] for r in cursor.fetchall()]


def init_db():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        # users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance BIGINT DEFAULT 2000,
                last_bonus INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0
            )
        ''')
        existing = _get_columns(cursor, 'users')
        if 'banned' not in existing:
            cursor.execute('ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0')
        if 'last_bonus_date' not in existing:
            cursor.execute('ALTER TABLE users ADD COLUMN last_bonus_date TEXT DEFAULT NULL')
        if 'last_quick_bonus' not in existing:
            cursor.execute('ALTER TABLE users ADD COLUMN last_quick_bonus TEXT DEFAULT NULL')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_stats (
                user_id BIGINT,
                game_type TEXT,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, game_type)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promos (
                code TEXT PRIMARY KEY,
                reward BIGINT,
                max_uses INTEGER,
                current_uses INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promo_history (
                code TEXT,
                user_id BIGINT,
                activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code, user_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                chat_id BIGINT PRIMARY KEY,
                chat_title TEXT,
                sub_required INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS required_subscriptions (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT UNIQUE,
                type TEXT,
                link TEXT,
                title TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                user_id BIGINT,
                chat_id BIGINT,
                confirmed INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, chat_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS moderators (
                user_id BIGINT PRIMARY KEY,
                role TEXT DEFAULT 'moderator',
                added_by BIGINT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # миграционные проверки для кланов
        clans_cols = _get_columns(cursor, 'clans')
        if clans_cols and 'id' not in clans_cols:
            cursor.execute('DROP TABLE IF EXISTS clans')
            cursor.execute('DROP TABLE IF EXISTS clan_members')
            cursor.execute('DROP TABLE IF EXISTS clan_requests')
        cm_cols = _get_columns(cursor, 'clan_members')
        if cm_cols and 'clan_id' not in cm_cols:
            cursor.execute('DROP TABLE IF EXISTS clan_members')
            cursor.execute('DROP TABLE IF EXISTS clan_requests')
        ce_cols = _get_columns(cursor, 'clan_emojis')
        if ce_cols and 'emoji_id' not in ce_cols:
            cursor.execute('DROP TABLE IF EXISTS clan_emojis')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clans (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE,
                emoji_id TEXT,
                emoji_fallback TEXT,
                leader_crown_id TEXT,
                leader_crown_fallback TEXT,
                leader_id BIGINT,
                treasury BIGINT DEFAULT 0,
                max_members INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        ccols = _get_columns(cursor, 'clans')
        if 'leader_crown_id' not in ccols:
            cursor.execute('ALTER TABLE clans ADD COLUMN leader_crown_id TEXT')
        if 'leader_crown_fallback' not in ccols:
            cursor.execute('ALTER TABLE clans ADD COLUMN leader_crown_fallback TEXT')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clan_members (
                clan_id INTEGER,
                user_id BIGINT UNIQUE,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (clan_id, user_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clan_requests (
                id SERIAL PRIMARY KEY,
                clan_id INTEGER,
                user_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clan_emojis (
                id SERIAL PRIMARY KEY,
                emoji_id TEXT UNIQUE,
                fallback TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clan_crowns (
                id SERIAL PRIMARY KEY,
                emoji_id TEXT UNIQUE,
                fallback TEXT
            )
        ''')

        cursor.execute(
            "INSERT INTO moderators (user_id, role, added_by) VALUES (%s, 'owner', %s) ON CONFLICT (user_id) DO NOTHING",
            (OWNER_ID, OWNER_ID))
        conn.commit()
        cursor.close()
        conn.close()


# ---------- КЛАНЫ: ХЕЛПЕРЫ ----------

def get_user_clan(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.name, c.emoji_id, c.emoji_fallback, c.leader_crown_id, c.leader_crown_fallback,
                   c.leader_id, c.treasury, c.max_members
            FROM clans c JOIN clan_members m ON c.id = m.clan_id
            WHERE m.user_id = %s
        ''', (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return dict(row) if row else None


def get_clan_by_id(clan_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clans WHERE id = %s', (clan_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return dict(row) if row else None


def get_clan_by_name(name):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clans WHERE LOWER(name) = LOWER(%s)', (name,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return dict(row) if row else None


def get_clan_members(clan_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM clan_members WHERE clan_id = %s ORDER BY joined_at', (clan_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]


def get_clan_member_count(clan_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) AS c FROM clan_members WHERE clan_id = %s', (clan_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row['c'] if row else 0


def get_all_clans():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clans ORDER BY created_at ASC')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]


def search_clans(query):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clans WHERE LOWER(name) LIKE LOWER(%s) ORDER BY name', (f'%{query}%',))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]


def create_clan(name, emoji_id, emoji_fallback, crown_id, crown_fallback, leader_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO clans (name, emoji_id, emoji_fallback, leader_crown_id, leader_crown_fallback, leader_id, max_members)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (name, emoji_id, emoji_fallback, crown_id, crown_fallback, leader_id, CLAN_BASE_SLOTS))
        clan_id = cursor.fetchone()['id']
        cursor.execute('INSERT INTO clan_members (clan_id, user_id) VALUES (%s, %s)', (clan_id, leader_id))
        conn.commit()
        cursor.close()
        conn.close()
        return clan_id


def delete_clan(clan_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clan_members WHERE clan_id = %s', (clan_id,))
        cursor.execute('DELETE FROM clan_requests WHERE clan_id = %s', (clan_id,))
        cursor.execute('DELETE FROM clans WHERE id = %s', (clan_id,))
        conn.commit()
        cursor.close()
        conn.close()


def add_clan_member(clan_id, user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO clan_members (clan_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING',
            (clan_id, user_id))
        conn.commit()
        cursor.close()
        conn.close()


def remove_clan_member(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clan_members WHERE user_id = %s', (user_id,))
        conn.commit()
        cursor.close()
        conn.close()


def expand_clan(clan_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE clans SET max_members = max_members + 1 WHERE id = %s', (clan_id,))
        conn.commit()
        cursor.close()
        conn.close()


def transfer_clan(clan_id, new_leader_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE clans SET leader_id = %s WHERE id = %s', (new_leader_id, clan_id))
        conn.commit()
        cursor.close()
        conn.close()


def add_clan_request(clan_id, user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM clan_requests WHERE clan_id = %s AND user_id = %s', (clan_id, user_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return False
        cursor.execute('INSERT INTO clan_requests (clan_id, user_id) VALUES (%s, %s)', (clan_id, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True


def remove_clan_request(clan_id, user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clan_requests WHERE clan_id = %s AND user_id = %s', (clan_id, user_id))
        conn.commit()
        cursor.close()
        conn.close()


def get_clan_emojis():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, emoji_id, fallback FROM clan_emojis ORDER BY id DESC')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]


def add_clan_emoji(emoji_id, fallback):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO clan_emojis (emoji_id, fallback) VALUES (%s, %s) ON CONFLICT (emoji_id) DO NOTHING',
                (emoji_id, fallback))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()


def clear_clan_emojis():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clan_emojis')
        conn.commit()
        cursor.close()
        conn.close()


def get_clan_crowns():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, emoji_id, fallback FROM clan_crowns ORDER BY id DESC')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]


def add_clan_crown(emoji_id, fallback):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO clan_crowns (emoji_id, fallback) VALUES (%s, %s) ON CONFLICT (emoji_id) DO NOTHING',
                (emoji_id, fallback))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()


def clear_clan_crowns():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clan_crowns')
        conn.commit()
        cursor.close()
        conn.close()


def render_clan_name(clan):
    if not clan:
        return ''
    e = ''
    if clan.get('emoji_id'):
        fallback = clan.get('emoji_fallback') or '🏰'
        e = f'<tg-emoji emoji-id="{clan["emoji_id"]}">{fallback}</tg-emoji>'
    return f'{e}<b>{clan["name"]}</b>'


def render_leader_crown(clan):
    if not clan:
        return ''
    if clan.get('leader_crown_id'):
        fallback = clan.get('leader_crown_fallback') or '👑'
        return f'<tg-emoji emoji-id="{clan["leader_crown_id"]}">{fallback}</tg-emoji>'
    return '👑'


def get_clean_name(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT first_name, username FROM users WHERE user_id = %s', (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            name = (row['first_name'] or '').strip() or (row['username'] or '').strip()
            if name:
                return name
        return f"id{user_id}"


# ---------- ОБЩИЕ ----------

def get_user_display(user):
    try:
        user_id = None
        name = None
        if hasattr(user, 'id') and hasattr(user, 'first_name'):
            user_id = user.id
            name = (getattr(user, 'first_name', '') or '').strip() or (getattr(user, 'username', '') or '').strip()
        elif hasattr(user, 'get') and callable(getattr(user, 'get')):
            user_id = user.get('user_id')
            name = (user.get('first_name') or '').strip() or (user.get('username') or '').strip()
        else:
            try:
                user_id = user['user_id']
            except Exception:
                user_id = None
            try:
                fn = user['first_name'] or ''
                un = user['username'] or ''
                name = fn.strip() or un.strip()
            except Exception:
                name = None
        if not user_id:
            return "Пользователь"
        if not name:
            with db_lock:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT first_name, username FROM users WHERE user_id = %s', (user_id,))
                row = cursor.fetchone()
                cursor.close()
                conn.close()
                if row:
                    name = (row['first_name'] or '').strip() or (row['username'] or '').strip()
        if not name:
            name = f"id{user_id}"
        clan = get_user_clan(user_id)
        if clan:
            prefix = ''
            if clan.get('emoji_id'):
                fallback = clan.get('emoji_fallback') or '🏰'
                prefix = f'<tg-emoji emoji-id="{clan["emoji_id"]}">{fallback}</tg-emoji> '
            return f'{prefix}<a href="tg://user?id={user_id}">{name}</a> <b>〘{clan["name"]}〙</b>'
        return f'<a href="tg://user?id={user_id}">{name}</a>'
    except Exception:
        return "Пользователь"


def get_user_display_by_id(user_id):
    user = get_or_create_user(user_id, "", "")
    return get_user_display(user)


def get_or_create_user(user_id, username, first_name):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, balance, banned, last_bonus_date)
                VALUES (%s, %s, %s, %s, 0, NULL)
            ''', (user_id, username, first_name, 2000))
            for game in ['dice', 'rps', 'ttt', 'mines', 'number']:
                cursor.execute('''
                    INSERT INTO game_stats (user_id, game_type, wins, losses)
                    VALUES (%s, %s, 0, 0) ON CONFLICT (user_id, game_type) DO NOTHING
                ''', (user_id, game))
            conn.commit()
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
        else:
            if username:
                cursor.execute('UPDATE users SET username = %s WHERE user_id = %s', (username, user_id))
            if first_name:
                cursor.execute('UPDATE users SET first_name = %s WHERE user_id = %s', (first_name, user_id))
            for game in ['dice', 'rps', 'ttt', 'mines', 'number']:
                cursor.execute('''
                    INSERT INTO game_stats (user_id, game_type, wins, losses)
                    VALUES (%s, %s, 0, 0) ON CONFLICT (user_id, game_type) DO NOTHING
                ''', (user_id, game))
            conn.commit()
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user


def is_banned(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT banned FROM users WHERE user_id = %s', (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row and row['banned'] == 1


def get_all_users():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, first_name, balance FROM users ORDER BY balance DESC')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows


def get_all_chats():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id, chat_title, sub_required FROM chats')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows


def add_chat(chat_id, title):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO chats (chat_id, chat_title) VALUES (%s, %s) ON CONFLICT (chat_id) DO NOTHING',
            (chat_id, title))
        cursor.execute('UPDATE chats SET chat_title = %s WHERE chat_id = %s', (title, chat_id))
        conn.commit()
        cursor.close()
        conn.close()


def update_balance(user_id, amount):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + %s WHERE user_id = %s', (amount, user_id))
        conn.commit()
        cursor.close()
        conn.close()


def set_balance(user_id, amount):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = %s WHERE user_id = %s', (amount, user_id))
        conn.commit()
        cursor.close()
        conn.close()


def update_game_stats(user_id, game_type, is_win):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        if is_win:
            cursor.execute('UPDATE game_stats SET wins = wins + 1 WHERE user_id = %s AND game_type = %s',
                           (user_id, game_type))
        else:
            cursor.execute('UPDATE game_stats SET losses = losses + 1 WHERE user_id = %s AND game_type = %s',
                           (user_id, game_type))
        conn.commit()
        cursor.close()
        conn.close()


def get_all_stats(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        for game in ['dice', 'rps', 'ttt', 'mines', 'number']:
            cursor.execute('''
                INSERT INTO game_stats (user_id, game_type, wins, losses)
                VALUES (%s, %s, 0, 0) ON CONFLICT (user_id, game_type) DO NOTHING
            ''', (user_id, game))
        conn.commit()
        cursor.execute('SELECT * FROM game_stats WHERE user_id = %s', (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        stats = {}
        names = {
            'dice': f'{EMO_DICE} Кости 1на1',
            'rps': f'{EMO_ROCK} Камень-Ножницы-Бумага',
            'ttt': f'{EMO_TTT_INVITE} Крестики-Нолики 3х3',
            'mines': f'{EMO_MINE} Минное поле 5x5',
            'number': f'{EMO_NUMBER} Угадай число'
        }
        for row in rows:
            game = row['game_type']
            if game in names:
                wins, losses = row['wins'], row['losses']
                total = wins + losses
                winrate = 0.0 if total == 0 else round(((wins - losses) / total) * 100, 1)
                stats[game] = {'name': names[game], 'wins': wins, 'losses': losses, 'winrate': winrate}
        for game in ['dice', 'rps', 'ttt', 'mines', 'number']:
            if game not in stats:
                stats[game] = {'name': names[game], 'wins': 0, 'losses': 0, 'winrate': 0.0}
        return stats


def update_streak(user_id, is_win, stake=0):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT current_streak, max_streak FROM users WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        if not res:
            cursor.close()
            conn.close()
            return
        current, maximum = res['current_streak'], res['max_streak']
        if is_win:
            if stake >= 1000:
                current += 1
                if current > maximum:
                    maximum = current
        else:
            current = 0
        cursor.execute('UPDATE users SET current_streak = %s, max_streak = %s WHERE user_id = %s',
                       (current, maximum, user_id))
        conn.commit()
        cursor.close()
        conn.close()


def check_banned(user_id, chat_id):
    if is_banned(user_id):
        user = get_or_create_user(user_id, "", "")
        display = get_user_display(user)
        safe_send(chat_id, f"{EMO_CANCEL} Вы забанены и не можете использовать бота, {display}.", parse_mode='HTML')
        return True
    return False


def check_pm_game(message):
    if message.chat.type == 'private':
        safe_send(message.chat.id,
                  f"{EMO_SOLO_HEADER} <b>Игры доступны только в чате!</b>\n\n"
                  f"Переходи в наш чат 👉 @Nox_chatik\n"
                  f"Там можно играть со всеми 💪",
                  parse_mode='HTML')
        return True
    return False


def get_moscow_date():
    return datetime.datetime.now(timezone(timedelta(hours=3))).strftime('%Y-%m-%d')


def get_quick_bonus_remaining(user):
    if not user['last_quick_bonus']:
        return 0
    try:
        last = datetime.datetime.fromisoformat(user['last_quick_bonus'])
    except Exception:
        return 0
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    elapsed = (now - last).total_seconds()
    remaining = QUICK_BONUS_INTERVAL - elapsed
    return max(0, int(remaining))


def format_time(seconds):
    seconds = int(seconds)
    m = seconds // 60
    s = seconds % 60
    if m > 0:
        return f"{m}м {s}с"
    return f"{s}с"


def build_balance_text(user):
    display = get_user_display(user)
    return f"{display}\n{EMO_NOX} <code>{user['balance']:,}</code> ноксов"


# ---------- ПОДПИСКИ ----------

def get_required_subscriptions():
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, chat_id, type, link, title FROM required_subscriptions')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(row) for row in rows]


def add_required_subscription(chat_id, type_, link, title):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            bot.get_chat(chat_id)
        except Exception as e:
            cursor.close()
            conn.close()
            raise Exception(f"Не удалось получить информацию о канале/чате: {e}")
        try:
            cursor.execute('''
                INSERT INTO required_subscriptions (chat_id, type, link, title)
                VALUES (%s, %s, %s, %s) ON CONFLICT (chat_id) DO NOTHING
            ''', (chat_id, type_, link, title))
            cursor.execute('DELETE FROM user_subscriptions WHERE chat_id = %s', (chat_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            raise Exception(f"Ошибка при добавлении подписки: {e}")
        cursor.close()
        conn.close()


def remove_required_subscription(sub_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT chat_id FROM required_subscriptions WHERE id = %s', (sub_id,))
            row = cursor.fetchone()
            chat_id = row['chat_id'] if row else None
            cursor.execute('DELETE FROM required_subscriptions WHERE id = %s', (sub_id,))
            if chat_id:
                cursor.execute('DELETE FROM user_subscriptions WHERE chat_id = %s', (chat_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            raise Exception(f"Ошибка при удалении подписки: {e}")
        cursor.close()
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
    if bid is not None and user_id == bid:
        return True
    try:
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT sub_required FROM chats WHERE chat_id = %s', (chat_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if not row or row['sub_required'] == 0:
                return True
    except Exception:
        return True
    subs = get_required_subscriptions()
    if not subs:
        return True
    not_confirmed = []
    for sub in subs:
        if is_user_subscribed_to_channel(user_id, sub['chat_id']):
            with db_lock:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_subscriptions (user_id, chat_id, confirmed)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (user_id, chat_id) DO UPDATE SET confirmed = 1
                ''', (user_id, sub['chat_id']))
                conn.commit()
                cursor.close()
                conn.close()
        else:
            not_confirmed.append(sub)
    if not_confirmed:
        key = (user_id, chat_id)
        unsub_attempts[key] = unsub_attempts.get(key, 0) + 1
        attempts = unsub_attempts[key]
        if attempts >= 5:
            unsub_attempts.pop(key, None)
            try:
                bot.ban_chat_member(chat_id, user_id)
                bot.unban_chat_member(chat_id, user_id)
                target_user = get_or_create_user(user_id, "", "")
                display = get_user_display(target_user)
                safe_send(chat_id, f"👢 {display} кикнут за 5 попыток писать без подписки!", parse_mode='HTML')
            except Exception as e:
                print(f"[KICK ERROR] {e}")
            return False
        if message_id:
            try:
                bot.delete_message(chat_id, message_id)
            except Exception:
                pass
        user = get_or_create_user(user_id, "", "")
        display = get_user_display(user)
        text = f"⚠️ <b>{display}</b>, для использования бота необходимо:\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for sub in not_confirmed:
            action = "вступить" if sub['type'] in ['group', 'supergroup'] else "подписаться"
            text += f"• <b>{sub['title']}</b> ({action})\n"
            link = sub['link']
            if not link.startswith('http'):
                if link.startswith('@'):
                    link = f'https://t.me/{link[1:]}'
                else:
                    link = f'https://t.me/{link}'
            markup.add(btn(f"📌 {sub['title']}", url=link, style='primary'))
        markup.add(btn("Я подписался/вступил", callback_data="check_subscribe", style='success'))
        remaining = 5 - attempts
        text += f"\nОсталось попыток: <b>{remaining}</b>"
        safe_send(chat_id, text, parse_mode='HTML', reply_markup=markup)
        return False
    else:
        unsub_attempts.pop((user_id, chat_id), None)
    return True


@bot.callback_query_handler(func=lambda call: call.data == "check_subscribe")
def handle_subscribe_check(call):
    try:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        if check_required_subscriptions(user_id, chat_id):
            try:
                bot.delete_message(chat_id, call.message.message_id)
            except:
                pass
            safe_answer(call.id, "✅ Подтверждено! Можете писать.")
        else:
            safe_answer(call.id, "❌ Вы ещё не выполнили все требования.", show_alert=True)
    except Exception as e:
        print(f"[ERROR] in check_subscribe: {e}")
        safe_answer(call.id, "❌ Ошибка! Попробуйте позже.", show_alert=True)


# ---------- ГЛАВНОЕ МЕНЮ ----------

def get_main_menu(user):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        btn("Профиль", callback_data="show_profile", style='success', icon=ICO_PROFILE),
        btn("Пополнить", callback_data="donate_menu", style='success', icon=ICO_DONATE)
    )
    markup.add(
        btn("Промокод", callback_data="enter_promo", style='primary', icon=ICO_PROMO),
        btn("Правила", callback_data="show_rules", style='primary', icon=ICO_RULES)
    )
    markup.add(
        btn("Наш канал", url="https://t.me/NoxHubs", style='danger', icon=ICO_CHANNEL),
        btn("Чатик", url="https://t.me/Nox_chatik", style='danger', icon=ICO_CHAT)
    )
    markup.add(
        btn("Поддержка", url=f"t.me/{OWNER_USERNAME}", style='danger', icon=ICO_SUPPORT)
    )
    if user['user_id'] == OWNER_ID:
        markup.add(btn("Админ-панель", callback_data="admin_panel", style='danger', icon=ICO_ADMIN))
    return markup


@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for new_user in message.new_chat_members:
        if new_user.is_bot:
            if new_user.id == get_bot_id():
                add_chat(message.chat.id, message.chat.title)
                safe_send(message.chat.id, f"{EMO_SAFE} Бот активирован в этом чате!", parse_mode='HTML')
            continue
        user = get_or_create_user(new_user.id, new_user.username, new_user.first_name)
        display = get_user_display(user)
        welcome_text = (
            f"{EMO_WELCOME} <b>Добро пожаловать в NoxHub, {display}!</b>\n\n"
            f"{EMO_BONUS} Стартовый баланс — 2000 ноксов {EMO_NOX}\n\n"
            f"<b>{EMO_RULES} ПРАВИЛА</b> — напишите <b>правила</b>\n\n"
            f"<b>{EMO_DICE} ИГРЫ</b> — команда <b>игры</b>\n\n"
            f"{EMO_PROFILE} <code>профиль</code> | {EMO_NOX} <code>б</code> | {EMO_TROPHY} <code>топ богатых</code>"
        )
        safe_send(message.chat.id, welcome_text, parse_mode='HTML')


@bot.message_handler(content_types=['left_chat_member'])
def handle_left_member(message):
    left_user = message.left_chat_member
    if left_user.is_bot:
        if left_user.id == get_bot_id():
            try:
                with db_lock:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM chats WHERE chat_id = %s', (message.chat.id,))
                    conn.commit()
                    cursor.close()
                    conn.close()
            except:
                pass
        return
    user_db = get_or_create_user(left_user.id, left_user.username, left_user.first_name)
    display_name = get_user_display(user_db)
    safe_send(message.chat.id, f"👋 {display_name} вышел из чата 🤦🏿‍♂️", parse_mode='HTML')


def donate_menu_start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(btn("За рубли", callback_data="donate_rubles", style='primary', icon=ICO_RUBLES))
    markup.add(btn("За звёзды", callback_data="donate_stars", style='success', icon=ICO_STARS))
    markup.add(btn("Назад", callback_data="back_to_menu", style='danger', icon=ICO_BACK))
    text = (
        f"{EMO_DONATE} <b>ПОПОЛНЕНИЕ БАЛАНСА</b>\n\n"
        "Выберите способ:\n\n"
        f"{EMO_RUBLES} <b>За рубли</b>\n   1 ₽ = 400 ноксов {EMO_NOX}\n   Минимум: 25 000\n\n"
        f"{EMO_STARS} <b>За звёзды</b>\n   1 звезда = 400 ноксов {EMO_NOX}\n   Минимум: 15 звёзд"
    )
    try:
        bot.send_photo(message.chat.id, BOT_PHOTO_URL, caption=text, reply_markup=markup, parse_mode='HTML')
    except:
        safe_send(message.chat.id, text, reply_markup=markup, parse_mode='HTML')


@bot.message_handler(commands=['start'])
def cmd_start(message):
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    args = message.text.split()
    if len(args) > 1 and args[1] == 'donate':
        donate_menu_start(message)
        return
    markup = get_main_menu(user)
    name = user['first_name'] or user['username'] or "Гость"
    text = f"{EMO_WELCOME} Добро пожаловать, {name}!\n\nМы рады видеть тебя в NoxHub.\nПриятного времяпрепровождения.\n\nВыбери раздел ниже {EMO_DOWN}"
    try:
        bot.send_photo(message.chat.id, BOT_PHOTO_URL, caption=text, reply_markup=markup, parse_mode='HTML')
    except:
        safe_send(message.chat.id, text, reply_markup=markup, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "show_rules")
def show_rules(call):
    text = (
        f"{EMO_RULES} <b>ПРАВИЛА NOXHUB</b>\n\n"
        f"{EMO_BULB} Для просмотра всех игр пропишите команду <b>игры</b>\n\n"
        f"<b>{EMO_BONUS} БОНУСЫ</b>\n"
        f"   {EMO_BULB} <code>бонус</code> — ежедневный + {QUICK_BONUS_AMOUNT} ноксов каждые 10 минут\n\n"
        f"<b>⚡ КОМАНДЫ</b>\n"
        f"   {EMO_PROFILE} <code>профиль</code>\n"
        f"   {EMO_NOX} <code>б</code> — баланс\n"
        f"   {EMO_TROPHY} <code>топ богатых</code>\n\n"
        f"💬 @Nox_chatik | {EMO_CHANNEL} @NoxHubs"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("Назад", callback_data="back_to_menu", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "show_profile")
def show_profile(call):
    user_id = call.from_user.id
    user = get_or_create_user(user_id, call.from_user.username, call.from_user.first_name)
    stats = get_all_stats(user_id)
    display = get_user_display(user)
    total_wins = sum(d['wins'] for d in stats.values())
    total_losses = sum(d['losses'] for d in stats.values())
    total_games = total_wins + total_losses
    total_winrate = 0.0 if total_games == 0 else round((total_wins / total_games) * 100, 1)
    text = f"{EMO_PROFILE} <b>ПРОФИЛЬ:</b> {display}\n"
    text += f"{EMO_NOX} <b>Баланс:</b> <code>{user['balance']:,}</code> ноксов\n"
    text += f"{EMO_FIRE} <b>Серия:</b> <code>{user['current_streak']}</code>\n"
    text += f"{EMO_TROPHY} <b>Рекорд:</b> <code>{user['max_streak']}</code>\n\n"
    text += f"📊 <b>ОБЩАЯ СТАТИСТИКА</b>\n"
    text += f"   🟢 {total_wins} | 🔴 {total_losses} | {EMO_MULT} {total_winrate}%\n"
    for game_type, data in stats.items():
        text += f"\n<b>{data['name']}</b>\n"
        text += f"   🟢 {data['wins']} | 🔴 {data['losses']} | {EMO_MULT} {data['winrate']}%\n"
    text += f"\n{EMO_BULB} Пополнить — кнопка «Пополнить»"
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("Назад", callback_data="back_to_menu", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    user = get_or_create_user(call.from_user.id, call.from_user.username, call.from_user.first_name)
    markup = get_main_menu(user)
    text = f"✨ Добро пожаловать в NoxHub!\nПриятного времяпрепровождения.\n\nВыбери раздел ниже {EMO_DOWN}"
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "enter_promo")
def enter_promo(call):
    msg = safe_send(call.message.chat.id, f"{EMO_PROMO} Введи промокод:", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_promo_redeem)
    safe_answer(call.id)


def process_promo_redeem(message):
    code = message.text.strip()
    user_id = message.from_user.id
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM promos WHERE code = %s', (code,))
        promo = cursor.fetchone()
        if not promo:
            safe_send(message.chat.id, f"{EMO_CANCEL} Промокод не найден.", parse_mode='HTML')
            cursor.close()
            conn.close()
            return
        cursor.execute('SELECT * FROM promo_history WHERE code = %s AND user_id = %s', (code, user_id))
        if cursor.fetchone():
            safe_send(message.chat.id, f"{EMO_CANCEL} Уже активирован!", parse_mode='HTML')
            cursor.close()
            conn.close()
            return
        if promo['current_uses'] >= promo['max_uses']:
            safe_send(message.chat.id, f"{EMO_CANCEL} Лимит исчерпан.", parse_mode='HTML')
            cursor.close()
            conn.close()
            return
        cursor.execute('UPDATE promos SET current_uses = current_uses + 1 WHERE code = %s', (code,))
        cursor.execute('INSERT INTO promo_history (code, user_id) VALUES (%s, %s)', (code, user_id))
        conn.commit()
        cursor.close()
        conn.close()
    update_balance(user_id, promo['reward'])
    safe_send(message.chat.id, f"{EMO_PROMO} +{promo['reward']:,} ноксов {EMO_NOX}", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "donate_menu")
def donate_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(btn("За рубли", callback_data="donate_rubles", style='primary', icon=ICO_RUBLES))
    markup.add(btn("За звёзды", callback_data="donate_stars", style='success', icon=ICO_STARS))
    markup.add(btn("Назад", callback_data="back_to_menu", style='danger', icon=ICO_BACK))
    text = (
        f"{EMO_DONATE} <b>ПОПОЛНЕНИЕ БАЛАНСА</b>\n\n"
        "Выберите способ оплаты:\n\n"
        f"{EMO_RUBLES} <b>За рубли</b>\n"
        f"   Курс: 1 ₽ = 400 ноксов {EMO_NOX}\n"
        f"   Минимум: 25 000 ноксов\n\n"
        f"{EMO_STARS} <b>За звёзды</b>\n"
        f"   Курс: 1 звезда = 400 ноксов {EMO_NOX}\n"
        f"   Минимум: 15 звёзд"
    )
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "donate_rubles")
def donate_rubles(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("Ввести сумму", callback_data="donate_input", style='primary', icon=ICO_INPUT))
    markup.add(btn("Назад", callback_data="donate_menu", style='danger', icon=ICO_BACK))
    text = (
        f"{EMO_RUBLES} <b>ПОПОЛНЕНИЕ ЗА РУБЛИ</b>\n\n"
        f"Курс: <b>1 ₽ = 400 ноксов {EMO_NOX}</b>\n"
        f"Минимум: <b>25 000 ноксов</b>"
    )
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "donate_input")
def donate_input(call):
    msg = safe_send(call.message.chat.id, f"{EMO_INPUT} Введи количество (мин 25 000):", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_donate_amount)
    safe_answer(call.id)


def process_donate_amount(message):
    user_id = message.from_user.id
    try:
        nox = int(message.text.strip())
        if nox < 25000:
            safe_send(message.chat.id, f"{EMO_CANCEL} Минимум 25 000!", parse_mode='HTML')
            return
        rub = round(nox / 400, 2)
        temp_donate[user_id] = {'nox': nox, 'rub': rub, 'type': 'rubles'}
        markup = types.InlineKeyboardMarkup()
        markup.add(btn("Оплатить", callback_data="donate_pay", style='success', icon=ICO_DONATE))
        markup.add(btn("Отмена", callback_data="donate_cancel", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"💳 Купить <b>{nox:,} ноксов {EMO_NOX}</b>?\n💰 <b>{rub} ₽</b>", reply_markup=markup, parse_mode='HTML')
    except ValueError:
        safe_send(message.chat.id, f"{EMO_CANCEL} Введи число!", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "donate_pay")
def donate_pay(call):
    user_id = call.from_user.id
    if user_id not in temp_donate:
        safe_answer(call.id, "❌ Данные устарели.", show_alert=True)
        return
    data = temp_donate.pop(user_id)
    nox = data['nox']
    rub = data['rub']
    text = f"💳 <b>Пополнение на {nox:,} ноксов {EMO_NOX}</b>\n\n"
    text += f"💰 Сумма: <b>{rub} ₽</b>\n"
    text += f"🏦 <b>Карта Т-Банк:</b> <code>{CARD_NUMBER}</code>\n\n"
    text += f"1️⃣ Переведи <b>{rub} ₽</b>\n"
    text += f"2️⃣ Скрин чека\n"
    text += f"3️⃣ Нажми «Я оплатил»"
    owner_text = f"💳 Оплатил {nox:,} ноксов ({rub} ₽). Чек прилагаю."
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
    text = (
        f"{EMO_STARS} <b>ПОПОЛНЕНИЕ ЗА ЗВЁЗДЫ</b>\n\n"
        f"Курс: <b>1 ⭐ = 400 ноксов {EMO_NOX}</b>\n"
        f"Минимум: <b>15 ⭐</b>"
    )
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "donate_stars_input")
def donate_stars_input(call):
    msg = safe_send(call.message.chat.id, f"{EMO_INPUT} Введи кол-во звёзд (мин 15):", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_donate_stars_amount)
    safe_answer(call.id)


def process_donate_stars_amount(message):
    user_id = message.from_user.id
    try:
        stars = int(message.text.strip())
        if stars < 15:
            safe_send(message.chat.id, f"{EMO_CANCEL} Минимум 15 ⭐!", parse_mode='HTML')
            return
        nox = stars * 400
        temp_donate[user_id] = {'stars': stars, 'nox': nox, 'type': 'stars'}
        markup = types.InlineKeyboardMarkup()
        markup.add(btn("Оплатить", callback_data="donate_stars_pay", style='success', icon=ICO_DONATE))
        markup.add(btn("Отмена", callback_data="donate_cancel", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_STARS} <b>{nox:,} ноксов {EMO_NOX}</b> за {stars} ⭐", reply_markup=markup, parse_mode='HTML')
    except ValueError:
        safe_send(message.chat.id, f"{EMO_CANCEL} Введи число!", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "donate_stars_pay")
def donate_stars_pay(call):
    user_id = call.from_user.id
    if user_id not in temp_donate:
        safe_answer(call.id, "❌ Данные устарели.", show_alert=True)
        return
    data = temp_donate.pop(user_id)
    stars = data['stars']
    nox = data['nox']
    text = f"{EMO_STARS} <b>{nox:,} ноксов {EMO_NOX}</b> за <b>{stars} ⭐</b>"
    owner_text = f"⭐ Оплатил {stars} звёзд ({nox:,} ноксов)."
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("Владельцу", url=f"tg://resolve?domain={OWNER_USERNAME}&text={owner_text}", style='success', icon=ICO_SUPPORT))
    markup.add(btn("Назад", callback_data="donate_stars", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "donate_cancel")
def donate_cancel(call):
    user_id = call.from_user.id
    if user_id in temp_donate:
        del temp_donate[user_id]
    safe_edit(call.message.chat.id, call.message.message_id, f"{EMO_CANCEL} Операция отменена.", parse_mode='HTML')
    safe_answer(call.id)


# ---------- СПИСОК ИГР ----------

def build_games_list():
    return (
        f"{EMO_DICE} <b>СПИСОК ДОСТУПНЫХ ИГР</b>\n\n"
        f"{EMO_PVP_HEADER} <b>ПВП ИГРЫ</b> {EMO_PVP_HEADER}\n\n"
        f"{EMO_DICE} <b>Кости 1на1</b> — <code>кости [ставка]</code>\n"
        f"{DIV_PVP_LINE}\n"
        f"{EMO_ROCK} <b>Камень-Ножницы-Бумага</b> — <code>цуефа [ставка]</code>\n"
        f"{DIV_PVP_LINE}\n"
        f"{EMO_TTT_INVITE} <b>Крестики-Нолики 3х3</b> — <code>крестики [ставка]</code>\n"
        f"{DIV_PVP_LINE}\n"
        f"{EMO_MINE} <b>Минное поле 5x5</b> — <code>мины [ставка]</code>\n"
        f"{DIV_PVP_LINE}\n"
        f"{EMO_NUMBER} <b>Угадай число</b> — <code>число [диапазон] [ставка]</code>\n"
        f"{DIV_PVP_LINE}\n"
        f"{EMO_ROULETTE} <b>Русская рулетка</b> — <code>рулетка [ставка]</code>\n"
        f"{DIV_PVP_LINE}\n"
        f"{EMO_EAGLE} <b>Орёл и решка</b> — <code>орел [ставка]</code> / <code>решка [ставка]</code>\n"
        f"{DIV_PVP_LINE}\n"
        f"{EMO_PVP_HEADER}\n\n"
        f"{EMO_SOLO_HEADER} <b>СОЛО ИГРЫ</b> {EMO_SOLO_HEADER}\n\n"
        f"{EMO_SLOTS} <b>Слоты</b> — <code>слот [ставка]</code>\n"
        f"{DIV_SOLO_LINE}\n"
        f"{EMO_CHEST} <b>Сундук</b> — <code>сундук [ставка]</code>\n"
        f"{DIV_SOLO_LINE}\n"
        f"{EMO_FLOOR} <b>Этажи</b> — <code>этажи [ставка]</code>\n"
        f"{DIV_SOLO_LINE}\n"
        f"{EMO_SOLO_HEADER}\n\n"
        f"{EMO_BULB} <i>Вместо ставки можно писать <b>вб</b> — поставит весь баланс</i>\n"
        f"{EMO_BULB} Для подробных правил напишите <b>правила</b>\n\n"
        f"{EMO_CLAN} <b>КЛАНЫ</b> — команды <code>кланы</code> / <code>клан</code>"
    )


@bot.callback_query_handler(func=lambda call: call.data == "show_games")
def show_games_callback(call):
    text = build_games_list()
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("Назад", callback_data="back_to_menu", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.message_handler(commands=['игры'])
@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'игры')
def cmd_list_games(message):
    safe_send(message.chat.id, build_games_list(), parse_mode='HTML')


# ---------- БАЛАНС / БОНУС ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'б')
def cmd_balance_short(message):
    try:
        if check_banned(message.from_user.id, message.chat.id):
            return
        if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id,
                                            sender_chat=message.sender_chat):
            return
        bot_username = bot.get_me().username
        user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        today = get_moscow_date()
        daily_taken = user['last_bonus_date'] == today
        quick_remaining = get_quick_bonus_remaining(user)

        if not daily_taken:
            bonus_label = "Бонус"
            bonus_icon = ICO_BONUS_ICO
        elif quick_remaining == 0:
            bonus_label = f"+{QUICK_BONUS_AMOUNT} ноксов"
            bonus_icon = ICO_GOLD_BTN
        else:
            bonus_label = f"Бонус {format_time(quick_remaining)}"
            bonus_icon = ICO_BONUS_ICO

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            btn("Пополнить", url=f"https://t.me/{bot_username}?start=donate", style='success', icon=ICO_DONATE),
            btn(bonus_label, callback_data=f"quick_bonus_{user['user_id']}", style='primary', icon=bonus_icon)
        )
        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            target_user = get_or_create_user(target_id, message.reply_to_message.from_user.username,
                                             message.reply_to_message.from_user.first_name)
            text = build_balance_text(target_user)
            safe_send(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
            return
        text = build_balance_text(user)
        safe_send(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"[BALANCE ERR] {e}")


def build_bonus_state(user):
    today = get_moscow_date()
    if user['last_bonus_date'] != today:
        return 0
    if get_quick_bonus_remaining(user) == 0:
        return 1
    return 2


def build_balance_keyboard(user):
    bot_username = bot.get_me().username
    today = get_moscow_date()
    daily_taken = user['last_bonus_date'] == today
    quick_remaining = get_quick_bonus_remaining(user)
    if not daily_taken:
        bonus_label = "Бонус"
        bonus_icon = ICO_BONUS_ICO
    elif quick_remaining == 0:
        bonus_label = f"+{QUICK_BONUS_AMOUNT} ноксов"
        bonus_icon = ICO_GOLD_BTN
    else:
        bonus_label = f"Бонус {format_time(quick_remaining)}"
        bonus_icon = ICO_BONUS_ICO
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        btn("Пополнить", url=f"https://t.me/{bot_username}?start=donate", style='success', icon=ICO_DONATE),
        btn(bonus_label, callback_data=f"quick_bonus_{user['user_id']}", style='primary', icon=bonus_icon)
    )
    return markup


@bot.callback_query_handler(func=lambda call: call.data.startswith("quick_bonus"))
def quick_bonus_handler(call):
    try:
        if call.data == "quick_bonus":
            user_id = call.from_user.id
        else:
            parts = call.data.split("_", 2)
            if len(parts) < 3:
                user_id = call.from_user.id
            else:
                try:
                    user_id = int(parts[2])
                except:
                    user_id = call.from_user.id
            if call.from_user.id != user_id:
                safe_answer(call.id, "🖕 Это не твоё сообщение, додик! Кнопка для другого 😂", show_alert=True)
                return

        user = get_or_create_user(user_id, call.from_user.username, call.from_user.first_name)
        state = build_bonus_state(user)

        if state == 0:
            bonus = random.randint(850, 1200)
            jackpot = False
            if random.random() * 10000 < 1:
                bonus = 50000
                jackpot = True
            today = get_moscow_date()
            with db_lock:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET balance = balance + %s, last_bonus_date = %s WHERE user_id = %s',
                               (bonus, today, user_id))
                conn.commit()
                cursor.close()
                conn.close()
            if jackpot:
                safe_answer(call.id, f"🎉 ДЖЕКПОТ! +{bonus:,} ноксов!", show_alert=True)
            else:
                safe_answer(call.id, f"🎁 Ежедневный бонус: +{bonus:,} ноксов!", show_alert=True)
            updated = get_or_create_user(user_id, "", "")
            new_text = build_balance_text(updated)
            new_markup = build_balance_keyboard(updated)
            try:
                safe_edit(call.message.chat.id, call.message.message_id, new_text, reply_markup=new_markup, parse_mode='HTML')
            except Exception:
                pass
        elif state == 1:
            now_iso = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat()
            with db_lock:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET balance = balance + %s, last_quick_bonus = %s WHERE user_id = %s',
                               (QUICK_BONUS_AMOUNT, now_iso, user_id))
                conn.commit()
                cursor.close()
                conn.close()
            safe_answer(call.id, f"💰 +{QUICK_BONUS_AMOUNT} ноксов!", show_alert=True)
            updated = get_or_create_user(user_id, "", "")
            new_text = build_balance_text(updated)
            new_markup = build_balance_keyboard(updated)
            try:
                safe_edit(call.message.chat.id, call.message.message_id, new_text, reply_markup=new_markup, parse_mode='HTML')
            except Exception:
                pass
        else:
            remaining = get_quick_bonus_remaining(user)
            safe_answer(call.id, f"⏱ Бонус будет доступен через {format_time(remaining)}", show_alert=True)
            updated = get_or_create_user(user_id, "", "")
            new_text = build_balance_text(updated)
            new_markup = build_balance_keyboard(updated)
            try:
                safe_edit(call.message.chat.id, call.message.message_id, new_text, reply_markup=new_markup, parse_mode='HTML')
            except Exception:
                pass
    except Exception as e:
        print(f"[QUICK BONUS ERR] {e}")
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
        safe_send(message.chat.id, f"{EMO_CANCEL} Формат: <code>п [сумма] @username</code>", parse_mode='HTML')
        return
    amount = int(parts[1])
    target_str = parts[2]
    if amount <= 0:
        safe_send(message.chat.id, f"{EMO_CANCEL} Сумма > 0!", parse_mode='HTML')
        return
    target_id = None
    if target_str.startswith('@'):
        username = target_str[1:]
        try:
            chat_member = bot.get_chat_member(message.chat.id, f"@{username}")
            target_id = chat_member.user.id
        except:
            safe_send(message.chat.id, f"{EMO_CANCEL} Пользователь не найден.", parse_mode='HTML')
            return
    else:
        try:
            target_id = int(target_str)
        except ValueError:
            try:
                chat_member = bot.get_chat_member(message.chat.id, f"@{target_str}")
                target_id = chat_member.user.id
            except:
                safe_send(message.chat.id, f"{EMO_CANCEL} Пользователь не найден.", parse_mode='HTML')
                return
    if target_id == message.from_user.id:
        safe_send(message.chat.id, f"{EMO_CANCEL} Самому себе нельзя!", parse_mode='HTML')
        return
    from_user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    to_user = get_or_create_user(target_id, "", "")
    if from_user['balance'] < amount:
        safe_send(message.chat.id, f"{EMO_CANCEL} Недостаточно баланса! Нужно <b>{amount:,}</b>, у тебя <b>{from_user['balance']:,}</b> ноксов {EMO_NOX}", parse_mode='HTML')
        return
    update_balance(from_user['user_id'], -amount)
    update_balance(to_user['user_id'], amount)
    from_display = get_user_display(from_user)
    to_display = get_user_display(to_user)
    safe_send(message.chat.id, f"{from_display} перевёл <b>{amount:,} ноксов {EMO_NOX}</b> {to_display}!", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and re.match(r'^п\s+\d+$', m.text.strip().lower()))
def cmd_transfer_short(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id,
                                        sender_chat=message.sender_chat):
        return
    if not message.reply_to_message:
        safe_send(message.chat.id, f"{EMO_CANCEL} Ответь на сообщение того, кому перевести.", parse_mode='HTML')
        return
    match = re.match(r'^п\s+(\d+)$', message.text.strip().lower())
    if not match:
        return
    amount = int(match.group(1))
    if amount <= 0:
        safe_send(message.chat.id, f"{EMO_CANCEL} Сумма > 0!", parse_mode='HTML')
        return
    from_user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    to_user = get_or_create_user(message.reply_to_message.from_user.id, message.reply_to_message.from_user.username,
                                 message.reply_to_message.from_user.first_name)
    if from_user['user_id'] == to_user['user_id']:
        safe_send(message.chat.id, f"{EMO_CANCEL} Самому себе нельзя!", parse_mode='HTML')
        return
    if from_user['balance'] < amount:
        safe_send(message.chat.id, f"{EMO_CANCEL} Недостаточно баланса! Нужно <b>{amount:,}</b>, у тебя <b>{from_user['balance']:,}</b> ноксов {EMO_NOX}", parse_mode='HTML')
        return
    update_balance(from_user['user_id'], -amount)
    update_balance(to_user['user_id'], amount)
    from_display = get_user_display(from_user)
    to_display = get_user_display(to_user)
    safe_send(message.chat.id, f"{from_display} перевёл <b>{amount:,} ноксов {EMO_NOX}</b> {to_display}!", parse_mode='HTML')


# ---------- ПРОФИЛЬ / ТОП ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'профиль')
def cmd_profile(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id,
                                        sender_chat=message.sender_chat):
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    stats = get_all_stats(user['user_id'])
    display = get_user_display(user)
    tw = sum(d['wins'] for d in stats.values())
    tl = sum(d['losses'] for d in stats.values())
    tg = tw + tl
    tr = 0.0 if tg == 0 else round((tw / tg) * 100, 1)
    text = f"{EMO_PROFILE} <b>ПРОФИЛЬ:</b> {display}\n"
    text += f"{EMO_NOX} <b>Баланс:</b> <code>{user['balance']:,}</code> ноксов\n"
    text += f"{EMO_FIRE} <b>Серия:</b> <code>{user['current_streak']}</code>\n"
    text += f"{EMO_TROPHY} <b>Рекорд:</b> <code>{user['max_streak']}</code>\n\n"
    text += f"📊 <b>ОБЩАЯ:</b> 🟢 {tw} | 🔴 {tl} | {EMO_MULT} {tr}%\n"
    for gt, d in stats.items():
        text += f"\n<b>{d['name']}</b>\n   🟢 {d['wins']} | 🔴 {d['losses']} | {EMO_MULT} {d['winrate']}%\n"
    safe_send(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'тп')
def cmd_other_profile(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id,
                                        sender_chat=message.sender_chat):
        return
    if not message.reply_to_message:
        safe_send(message.chat.id, f"{EMO_CANCEL} Ответь на сообщение!", parse_mode='HTML')
        return
    tid = message.reply_to_message.from_user.id
    tu = get_or_create_user(tid, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
    stats = get_all_stats(tid)
    display = get_user_display(tu)
    tw = sum(d['wins'] for d in stats.values())
    tl = sum(d['losses'] for d in stats.values())
    tg = tw + tl
    tr = 0.0 if tg == 0 else round((tw / tg) * 100, 1)
    text = f"{EMO_PROFILE} <b>ПРОФИЛЬ:</b> {display}\n"
    text += f"{EMO_NOX} <b>Баланс:</b> <code>{tu['balance']:,}</code> ноксов\n"
    text += f"{EMO_FIRE} <b>Серия:</b> <code>{tu['current_streak']}</code>\n"
    text += f"{EMO_TROPHY} <b>Рекорд:</b> <code>{tu['max_streak']}</code>\n\n"
    text += f"📊 <b>ОБЩАЯ:</b> 🟢 {tw} | 🔴 {tl} | {EMO_MULT} {tr}%\n"
    for gt, d in stats.items():
        text += f"\n<b>{d['name']}</b>\n   🟢 {d['wins']} | 🔴 {d['losses']} | {EMO_MULT} {d['winrate']}%\n"
    safe_send(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'правила')
def cmd_rules(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id,
                                        sender_chat=message.sender_chat):
        return
    text = f"{EMO_RULES} <b>ПРАВИЛА ДЛЯ УЧАСТНИКОВ</b>\n\n"
    text += "<i>Обязательны для всех. За нарушение — мут.</i>\n\n"
    text += f"{EMO_CANCEL} <b>ЗАПРЕЩЕНО</b>\n"
    text += f"• 18+ — <i>мут 2ч</i>\n"
    text += f"• Жесть — <i>мут 2ч</i>\n"
    text += f"• Спам — <i>мут 2ч</i>\n"
    text += f"• Реклама — <i>мут 10ч</i>\n"
    text += f"• Оскорбление модеров — <i>мут 30м</i>\n\n"
    text += f"{EMO_SAFE} <b>РАЗРЕШЕНО</b>\n"
    text += "• Оскорбления\n"
    text += "• Капс\n"
    text += "• Политика/религия\n"
    text += "• Токсичность\n\n"
    text += f"{EMO_REPORT} <b>ЖАЛОБЫ</b> — пишите модераторам.\n"
    text += f"{EMO_BULB} Для просмотра всех игр пропишите команду <b>игры</b>"
    safe_send(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'бонус')
def cmd_bonus(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id,
                                        sender_chat=message.sender_chat):
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    today = get_moscow_date()
    daily_taken = user['last_bonus_date'] == today
    quick_remaining = get_quick_bonus_remaining(user)
    if not daily_taken:
        bonus_label = "Забрать ежедневный бонус"
        bonus_icon = ICO_BONUS_ICO
    elif quick_remaining == 0:
        bonus_label = f"Забрать +{QUICK_BONUS_AMOUNT} ноксов"
        bonus_icon = ICO_GOLD_BTN
    else:
        bonus_label = f"Бонус {format_time(quick_remaining)}"
        bonus_icon = ICO_BONUS_ICO
    markup = types.InlineKeyboardMarkup()
    markup.add(btn(bonus_label, callback_data=f"quick_bonus_{user['user_id']}", style='success', icon=bonus_icon))
    text = (
        f"{EMO_BONUS} <b>БОНУСЫ NOXHUB</b>\n\n"
        f"1️⃣ Ежедневный — 850-1200 ноксов {EMO_NOX}\n"
        f"2️⃣ Каждые 10 минут — +{QUICK_BONUS_AMOUNT} ноксов {EMO_NOX}\n\n"
        f"{EMO_BULB} Нажми кнопку ниже!"
    )
    safe_send(message.chat.id, text, reply_markup=markup, parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'топ богатых')
def cmd_top(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id,
                                        sender_chat=message.sender_chat):
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, first_name, balance FROM users ORDER BY balance DESC LIMIT 10')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    if not rows:
        safe_send(message.chat.id, f"{EMO_CANCEL} Нет пользователей.", parse_mode='HTML')
        return
    text = f"{EMO_TROPHY} <b>ТОП-10 БОГАТЫХ</b>\n\n"
    for i, row in enumerate(rows, 1):
        u = dict(row)
        text += f"{i}. {get_user_display(u)}\n"
        text += f"   {EMO_NOX}: <code>{u['balance']:,}</code> ноксов\n"
    safe_send(message.chat.id, text, parse_mode='HTML')


# ---------- КЛАНЫ ----------

def build_clans_list_text(page=0):
    try:
        clans = get_all_clans()
        if not clans:
            return f"{EMO_CLAN_HEADER} <b>СПИСОК КЛАНОВ</b>\n\n<i>Пока нет ни одного клана.</i>", None
        per_page = 10
        total_pages = max(1, (len(clans) + per_page - 1) // per_page)
        page = max(0, min(page, total_pages - 1))
        start = page * per_page
        chunk = clans[start:start + per_page]
        text = f"{EMO_CLAN_HEADER} <b>СПИСОК КЛАНОВ</b> (стр. {page+1}/{total_pages})\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, c in enumerate(chunk, start=start + 1):
            members = get_clan_member_count(c['id'])
            crown = render_leader_crown(c)
            name_render = render_clan_name(c)
            text += f"{i}. {crown} {name_render} — {members}/{c['max_members']}\n"
            markup.add(btn(f"{c['name']} ({members}/{c['max_members']})", callback_data=f"clan_info_{c['id']}", style='primary'))
        nav = []
        if page > 0:
            nav.append(btn("◀️", callback_data=f"clans_page_{page-1}", style='primary'))
        if page < total_pages - 1:
            nav.append(btn("▶️", callback_data=f"clans_page_{page+1}", style='primary'))
        if nav:
            markup.row(*nav)
        markup.add(btn("🔍 Поиск по названию", callback_data="clan_search_start", style='primary'))
        return text, markup
    except Exception as e:
        print(f"[CLANS LIST ERR] {e}")
        return f"{EMO_CANCEL} Ошибка загрузки списка кланов: {e}", None


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'кланы')
def cmd_clans(message):
    try:
        text, markup = build_clans_list_text(0)
        safe_send(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"[CLANS CMD ERR] {e}")
        safe_send(message.chat.id, f"{EMO_CANCEL} Ошибка команды кланы: {e}", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data.startswith("clans_page_"))
def clans_page_cb(call):
    page = int(call.data.split("_")[2])
    text, markup = build_clans_list_text(page)
    safe_edit(call.message.chat.id, call.message.message_id, text, parse_mode='HTML', reply_markup=markup)
    safe_answer(call.id)


def build_my_clan_text(user_id):
    clan = get_user_clan(user_id)
    if not clan:
        text = f"{EMO_CLAN_HEADER} <b>МОЙ КЛАН</b>\n\n<i>У тебя нет клана.</i>"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(btn(f"🟢 Создать клан — {CLAN_CREATE_COST:,}", callback_data="clan_create_start", style='success'))
        return text, markup
    members = get_clan_members(clan['id'])
    is_leader = (user_id == clan['leader_id'])
    crown = render_leader_crown(clan)
    emoji_prefix = ''
    if clan.get('emoji_id'):
        fallback = clan.get('emoji_fallback') or '🏰'
        emoji_prefix = f'<tg-emoji emoji-id="{clan["emoji_id"]}">{fallback}</tg-emoji>'
    text = f"{emoji_prefix}<b>{clan['name']}</b>\n"
    text += f"{crown} Лидер: {get_user_display_by_id(clan['leader_id'])}\n"
    text += f"👥 Участники: {len(members)}/{clan['max_members']}\n"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(btn("👥 Участники", callback_data=f"clan_members_{clan['id']}", style='primary'))
    if is_leader:
        markup.add(btn(f"➕ Расширить — {CLAN_SLOT_COST:,}", callback_data=f"clan_expand_{clan['id']}", style='primary'))
        markup.add(btn("👑 Передать клан", callback_data=f"clan_transfer_{clan['id']}", style='primary'))
        markup.add(btn("🗑 Распустить клан", callback_data=f"clan_disband_{clan['id']}", style='danger'))
    else:
        markup.add(btn("🔴 Выйти из клана", callback_data=f"clan_leave_{clan['id']}", style='danger'))
    return text, markup


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() in ('клан', 'мой клан'))
def cmd_my_clan(message):
    try:
        text, markup = build_my_clan_text(message.from_user.id)
        safe_send(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"[MYCLAN ERR] {e}")
        safe_send(message.chat.id, f"{EMO_CANCEL} Ошибка: {e}", parse_mode='HTML')


# ----- СОЗДАНИЕ КЛАНА -----

@bot.callback_query_handler(func=lambda call: call.data == "clan_create_start")
def clan_create_start(cb):
    user_id = cb.from_user.id
    if get_user_clan(user_id):
        safe_answer(cb.id, "❌ У тебя уже есть клан!", show_alert=True)
        return
    user = get_or_create_user(user_id, "", "")
    if user['balance'] < CLAN_CREATE_COST:
        safe_answer(cb.id, f"❌ Недостаточно! Нужно {CLAN_CREATE_COST:,}, у тебя {user['balance']:,}", show_alert=True)
        return
    show_clan_emoji_picker(cb.message.chat.id, cb.message.message_id, 0)
    safe_answer(cb.id)


def show_clan_emoji_picker(chat_id, message_id, page):
    emojis = get_clan_emojis()
    if not emojis:
        safe_edit(chat_id, message_id,
                  f"{EMO_CLAN_HEADER} <b>СОЗДАНИЕ КЛАНА</b>\n\n❌ Нет загруженных символов. Обратитесь к админу.",
                  parse_mode='HTML')
        return
    per_page = CLAN_EMOJI_PER_PAGE
    total_pages = max(1, (len(emojis) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    chunk = emojis[page * per_page:(page + 1) * per_page]
    text = (f"{EMO_CLAN_HEADER} <b>СОЗДАНИЕ КЛАНА</b>\n"
            f"{EMO_NOX} Цена: <b>{CLAN_CREATE_COST:,}</b> ноксов\n\n"
            f"Выбери символ клана (стр. {page+1}/{total_pages}):")
    markup = types.InlineKeyboardMarkup(row_width=5)
    row = []
    for e in chunk:
        eid = e['id']
        row.append(btn(' ', callback_data=f"clan_emoji_pick_{eid}", style='primary', icon=e['emoji_id']))
        if len(row) == 5:
            markup.row(*row)
            row = []
    if row:
        markup.row(*row)
    nav = []
    if page > 0:
        nav.append(btn("◀️", callback_data=f"clan_pick_page_{page-1}", style='primary'))
    if page < total_pages - 1:
        nav.append(btn("▶️", callback_data=f"clan_pick_page_{page+1}", style='primary'))
    if nav:
        markup.row(*nav)
    markup.add(btn("Отмена", callback_data="clan_create_cancel", style='danger'))
    safe_edit(chat_id, message_id, text, parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_pick_page_"))
def clan_pick_page(call):
    page = int(call.data.split("_")[3])
    show_clan_emoji_picker(call.message.chat.id, call.message.message_id, page)
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "clan_create_cancel")
def clan_create_cancel(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    safe_answer(call.id, "Отменено")


@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_emoji_pick_"))
def clan_emoji_pick(call):
    user_id = call.from_user.id
    if get_user_clan(user_id):
        safe_answer(call.id, "❌ У тебя уже есть клан!", show_alert=True)
        return
    try:
        emoji_row_id = int(call.data.split("_")[3])
    except Exception:
        safe_answer(call.id, "❌", show_alert=True)
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT emoji_id, fallback FROM clan_emojis WHERE id = %s', (emoji_row_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
    if not row:
        safe_answer(call.id, "❌ Символ не найден", show_alert=True)
        return
    if 'clan_create_temp' not in globals():
        globals()['clan_create_temp'] = {}
    globals()['clan_create_temp'][user_id] = {
        'emoji_id': row['emoji_id'],
        'emoji_fallback': row['fallback']
    }
    show_clan_crown_picker(call.message.chat.id, call.message.message_id, 0)
    safe_answer(call.id)


def show_clan_crown_picker(chat_id, message_id, page):
    crowns = get_clan_crowns()
    if not crowns:
        safe_edit(chat_id, message_id,
                  f"👑 <b>ВЫБЕРИ КОРОНУ ЛИДЕРА</b>\n\n❌ Нет загруженных корон. Обратитесь к админу.",
                  parse_mode='HTML')
        return
    per_page = CLAN_EMOJI_PER_PAGE
    total_pages = max(1, (len(crowns) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    chunk = crowns[page * per_page:(page + 1) * per_page]
    text = (f"👑 <b>ВЫБЕРИ КОРОНУ ЛИДЕРА</b>\n\n"
            f"Стр. {page+1}/{total_pages}:")
    markup = types.InlineKeyboardMarkup(row_width=5)
    row = []
    for e in chunk:
        eid = e['id']
        row.append(btn(' ', callback_data=f"clan_crown_pick_{eid}", style='primary', icon=e['emoji_id']))
        if len(row) == 5:
            markup.row(*row)
            row = []
    if row:
        markup.row(*row)
    nav = []
    if page > 0:
        nav.append(btn("◀️", callback_data=f"clan_crown_page_{page-1}", style='primary'))
    if page < total_pages - 1:
        nav.append(btn("▶️", callback_data=f"clan_crown_page_{page+1}", style='primary'))
    if nav:
        markup.row(*nav)
    markup.add(btn("Отмена", callback_data="clan_create_cancel", style='danger'))
    safe_edit(chat_id, message_id, text, parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_crown_page_"))
def clan_crown_page(call):
    page = int(call.data.split("_")[3])
    show_clan_crown_picker(call.message.chat.id, call.message.message_id, page)
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_crown_pick_"))
def clan_crown_pick(call):
    user_id = call.from_user.id
    if get_user_clan(user_id):
        safe_answer(call.id, "❌ У тебя уже есть клан!", show_alert=True)
        return
    try:
        crown_row_id = int(call.data.split("_")[3])
    except Exception:
        safe_answer(call.id, "❌", show_alert=True)
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT emoji_id, fallback FROM clan_crowns WHERE id = %s', (crown_row_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
    if not row:
        safe_answer(call.id, "❌ Корона не найдена", show_alert=True)
        return
    temp = globals().get('clan_create_temp', {})
    if user_id not in temp:
        safe_answer(call.id, "❌ Сначала выбери символ клана", show_alert=True)
        return
    temp[user_id]['crown_id'] = row['emoji_id']
    temp[user_id]['crown_fallback'] = row['fallback']
    msg = safe_send(call.message.chat.id,
                    f"✍️ Напиши название клана в чат\n<i>(до 20 символов)</i>",
                    parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_clan_name)
    safe_answer(call.id)


def process_clan_name(message):
    user_id = message.from_user.id
    name = (message.text or "").strip()
    temp = globals().get('clan_create_temp', {})
    picked = temp.get(user_id)
    if not picked or 'emoji_id' not in picked or 'crown_id' not in picked:
        safe_send(message.chat.id, f"{EMO_CANCEL} Ошибка. Начни заново.", parse_mode='HTML')
        return
    if not name or len(name) > 20:
        safe_send(message.chat.id, f"{EMO_CANCEL} Название 1-20 символов.", parse_mode='HTML')
        return
    if get_clan_by_name(name):
        safe_send(message.chat.id, f"{EMO_CANCEL} Такое название уже занято.", parse_mode='HTML')
        return
    if get_user_clan(user_id):
        safe_send(message.chat.id, f"{EMO_CANCEL} У тебя уже есть клан.", parse_mode='HTML')
        return
    user = get_or_create_user(user_id, "", "")
    if user['balance'] < CLAN_CREATE_COST:
        safe_send(message.chat.id, f"{EMO_CANCEL} Недостаточно! Нужно {CLAN_CREATE_COST:,}, у тебя {user['balance']:,}.", parse_mode='HTML')
        return
    update_balance(user_id, -CLAN_CREATE_COST)
    create_clan(name, picked['emoji_id'], picked['emoji_fallback'],
                picked['crown_id'], picked['crown_fallback'], user_id)
    temp.pop(user_id, None)
    emoji_html = f'<tg-emoji emoji-id="{picked["emoji_id"]}">{picked["emoji_fallback"] or "🏰"}</tg-emoji>'
    crown_html = f'<tg-emoji emoji-id="{picked["crown_id"]}">{picked["crown_fallback"] or "👑"}</tg-emoji>'
    safe_send(message.chat.id,
              f"{EMO_SAFE} Клан {emoji_html}<b>{name}</b> создан!\n"
              f"{crown_html} Ты лидер\n"
              f"👥 Участники: 1/{CLAN_BASE_SLOTS}\n"
              f"{EMO_NOX} Списано: <b>{CLAN_CREATE_COST:,}</b> ноксов",
              parse_mode='HTML')


# ----- ИНФО О КЛАНЕ -----

@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_info_"))
def clan_info_cb(call):
    clan_id = int(call.data.split("_")[2])
    clan = get_clan_by_id(clan_id)
    if not clan:
        safe_answer(call.id, "❌ Клан не найден", show_alert=True)
        return
    members_count = get_clan_member_count(clan_id)
    crown = render_leader_crown(clan)
    emoji_prefix = ''
    if clan.get('emoji_id'):
        fallback = clan.get('emoji_fallback') or '🏰'
        emoji_prefix = f'<tg-emoji emoji-id="{clan["emoji_id"]}">{fallback}</tg-emoji>'
    text = f"{emoji_prefix}<b>{clan['name']}</b>\n"
    text += f"{crown} Лидер: {get_user_display_by_id(clan['leader_id'])}\n"
    text += f"👥 Участники: {members_count}/{clan['max_members']}\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    user_clan = get_user_clan(call.from_user.id)
    if user_clan and user_clan['id'] == clan_id:
        markup.add(btn("Это твой клан", callback_data="ignore", style='success'))
    elif user_clan:
        markup.add(btn("❌ Ты уже в другом клане", callback_data="ignore", style='danger'))
    elif members_count >= clan['max_members']:
        markup.add(btn("❌ Мест нет", callback_data="ignore", style='danger'))
    else:
        markup.add(btn("🟢 Вступить", callback_data=f"clan_join_{clan_id}", style='success'))
    safe_edit(call.message.chat.id, call.message.message_id, text, parse_mode='HTML', reply_markup=markup)
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "clan_search_start")
def clan_search_start(call):
    msg = safe_send(call.message.chat.id, "🔍 <b>Поиск клана</b>\n✍️ Напиши название (или часть) в чат:", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_clan_search)
    safe_answer(call.id)


def process_clan_search(message):
    q = (message.text or "").strip()
    if not q:
        return
    results = search_clans(q)
    if not results:
        safe_send(message.chat.id, f"{EMO_CANCEL} Клан не найден по запросу «{q}».", parse_mode='HTML')
        return
    text = f"🔍 <b>РЕЗУЛЬТАТЫ ПОИСКА</b> ({len(results)}):\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for c in results[:20]:
        m = get_clan_member_count(c['id'])
        crown = render_leader_crown(c)
        name_render = render_clan_name(c)
        text += f"• {crown} {name_render} — {m}/{c['max_members']}\n"
        markup.add(btn(f"{c['name']} ({m}/{c['max_members']})", callback_data=f"clan_info_{c['id']}", style='primary'))
    safe_send(message.chat.id, text, parse_mode='HTML', reply_markup=markup)


# ----- ЗАЯВКА В КЛАН -----

@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_join_"))
def clan_join_cb(call):
    user_id = call.from_user.id
    clan_id = int(call.data.split("_")[2])
    clan = get_clan_by_id(clan_id)
    if not clan:
        safe_answer(call.id, "❌ Клан не найден", show_alert=True)
        return
    if get_user_clan(user_id):
        safe_answer(call.id, "❌ Ты уже в клане!", show_alert=True)
        return
    if get_clan_member_count(clan_id) >= clan['max_members']:
        safe_answer(call.id, "❌ Мест нет", show_alert=True)
        return
    ok = add_clan_request(clan_id, user_id)
    if not ok:
        safe_answer(call.id, "⏳ Заявка уже отправлена", show_alert=True)
        return
    requester = get_or_create_user(user_id, call.from_user.username, call.from_user.first_name)
    req_display = get_user_display(requester)
    crown = render_leader_crown(clan)
    emoji_prefix = ''
    if clan.get('emoji_id'):
        fallback = clan.get('emoji_fallback') or '🏰'
        emoji_prefix = f'<tg-emoji emoji-id="{clan["emoji_id"]}">{fallback}</tg-emoji>'
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        btn("🟢 Подтвердить", callback_data=f"clan_req_ok_{clan_id}_{user_id}", style='success'),
        btn("🔴 Отклонить", callback_data=f"clan_req_no_{clan_id}_{user_id}", style='danger')
    )
    safe_send(call.message.chat.id,
              f"{EMO_REPORT} <b>ЗАЯВКА В КЛАН</b>\n\n"
              f"👤 {req_display} хочет вступить в клан {emoji_prefix}<b>{clan['name']}</b>\n\n"
              f"Лидер {crown}: подтверди или отклони",
              parse_mode='HTML', reply_markup=markup)
    safe_answer(call.id, "⏳ Заявка отправлена", show_alert=False)


@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_req_ok_"))
def clan_req_ok(call):
    parts = call.data.split("_")
    clan_id = int(parts[3])
    user_id = int(parts[4])
    clan = get_clan_by_id(clan_id)
    if not clan:
        safe_answer(call.id, "❌", show_alert=True)
        return
    if call.from_user.id != clan['leader_id']:
        safe_answer(call.id, "❌ Только лидер", show_alert=True)
        return
    if get_clan_member_count(clan_id) >= clan['max_members']:
        safe_answer(call.id, "❌ Мест нет", show_alert=True)
        return
    if get_user_clan(user_id):
        remove_clan_request(clan_id, user_id)
        safe_answer(call.id, "Уже в другом клане", show_alert=True)
        return
    add_clan_member(clan_id, user_id)
    remove_clan_request(clan_id, user_id)
    safe_answer(call.id, "✅ Принят")
    try:
        bot.send_message(user_id, f"✅ Тебя приняли в клан {render_clan_name(clan)}!", parse_mode='HTML')
    except Exception:
        pass
    try:
        safe_edit(call.message.chat.id, call.message.message_id,
                  f"✅ {get_user_display_by_id(user_id)} принят в клан.",
                  parse_mode='HTML')
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_req_no_"))
def clan_req_no(call):
    parts = call.data.split("_")
    clan_id = int(parts[3])
    user_id = int(parts[4])
    clan = get_clan_by_id(clan_id)
    if not clan:
        safe_answer(call.id, "❌", show_alert=True)
        return
    if call.from_user.id != clan['leader_id']:
        safe_answer(call.id, "❌ Только лидер", show_alert=True)
        return
    remove_clan_request(clan_id, user_id)
    safe_answer(call.id, "❌ Отклонено")
    try:
        bot.send_message(user_id, f"❌ Заявка в клан {render_clan_name(clan)} отклонена.", parse_mode='HTML')
    except Exception:
        pass
    try:
        safe_edit(call.message.chat.id, call.message.message_id,
                  f"❌ Заявка {get_user_display_by_id(user_id)} отклонена.",
                  parse_mode='HTML')
    except Exception:
        pass


# ----- УЧАСТНИКИ -----

@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_members_"))
def clan_members_cb(call):
    clan_id = int(call.data.split("_")[2])
    clan = get_clan_by_id(clan_id)
    if not clan:
        safe_answer(call.id, "❌", show_alert=True)
        return
    members = get_clan_members(clan_id)
    crown = render_leader_crown(clan)
    emoji_prefix = ''
    if clan.get('emoji_id'):
        fallback = clan.get('emoji_fallback') or '🏰'
        emoji_prefix = f'<tg-emoji emoji-id="{clan["emoji_id"]}">{fallback}</tg-emoji>'
    text = f"{emoji_prefix}<b>{clan['name']}</b>\n"
    text += f"👥 {len(members)}/{clan['max_members']}\n\n"
    text += f"{crown} <b>Лидер:</b>\n"
    text += f"• {get_user_display_by_id(clan['leader_id'])}\n\n"
    others = [m for m in members if m['user_id'] != clan['leader_id']]
    if others:
        text += f"<b>Участники:</b>\n"
        for m in others:
            text += f"• {get_user_display_by_id(m['user_id'])}\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("Назад", callback_data=f"clan_back_{clan_id}", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, parse_mode='HTML', reply_markup=markup)
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_back_"))
def clan_back_cb(call):
    text, markup = build_my_clan_text(call.from_user.id)
    safe_edit(call.message.chat.id, call.message.message_id, text, parse_mode='HTML', reply_markup=markup)
    safe_answer(call.id)


# ----- РАСШИРЕНИЕ -----

@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_expand_") and not call.data.startswith("clan_expand_ok_"))
def clan_expand_cb(call):
    clan_id = int(call.data.split("_")[2])
    clan = get_clan_by_id(clan_id)
    if not clan:
        safe_answer(call.id, "❌", show_alert=True)
        return
    if call.from_user.id != clan['leader_id']:
        safe_answer(call.id, "❌ Только лидер может расширять", show_alert=True)
        return
    user = get_or_create_user(call.from_user.id, "", "")
    text = (f"➕ <b>Расширение клана</b>\n\n"
            f"👥 Сейчас: {clan['max_members']}/{clan['max_members']}\n"
            f"➕ Станет: {clan['max_members']+1}/{clan['max_members']+1}\n"
            f"{EMO_NOX} Цена: <b>{CLAN_SLOT_COST:,}</b> ноксов\n"
            f"💳 Твой баланс: <code>{user['balance']:,}</code>")
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        btn("🟢 Подтвердить", callback_data=f"clan_expand_ok_{clan_id}", style='success'),
        btn("🔴 Отмена", callback_data=f"clan_back_{clan_id}", style='danger')
    )
    safe_edit(call.message.chat.id, call.message.message_id, text, parse_mode='HTML', reply_markup=markup)
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_expand_ok_"))
def clan_expand_ok(call):
    clan_id = int(call.data.split("_")[3])
    clan = get_clan_by_id(clan_id)
    if not clan:
        safe_answer(call.id, "❌", show_alert=True)
        return
    if call.from_user.id != clan['leader_id']:
        safe_answer(call.id, "❌ Только лидер", show_alert=True)
        return
    user = get_or_create_user(call.from_user.id, "", "")
    if user['balance'] < CLAN_SLOT_COST:
        safe_answer(call.id, f"❌ Недостаточно! Нужно {CLAN_SLOT_COST:,}, у тебя {user['balance']:,}", show_alert=True)
        return
    update_balance(call.from_user.id, -CLAN_SLOT_COST)
    expand_clan(clan_id)
    new_clan = get_clan_by_id(clan_id)
    safe_answer(call.id, f"✅ +1 место! Теперь {new_clan['max_members']}", show_alert=True)
    text, markup = build_my_clan_text(call.from_user.id)
    safe_edit(call.message.chat.id, call.message.message_id, text, parse_mode='HTML', reply_markup=markup)


# ----- ПЕРЕДАЧА КЛАНА -----

@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_transfer_") and not call.data.startswith("clan_transfer_to_"))
def clan_transfer_cb(call):
    try:
        clan_id = int(call.data.split("_")[2])
    except (ValueError, IndexError):
        safe_answer(call.id, "❌", show_alert=True)
        return
    clan = get_clan_by_id(clan_id)
    if not clan:
        safe_answer(call.id, "❌", show_alert=True)
        return
    if call.from_user.id != clan['leader_id']:
        safe_answer(call.id, "❌ Только лидер", show_alert=True)
        return
    members = get_clan_members(clan_id)
    others = [m for m in members if m['user_id'] != clan['leader_id']]
    if not others:
        safe_answer(call.id, "❌ В клане нет других участников", show_alert=True)
        return
    text = f"👑 <b>ПЕРЕДАТЬ КЛАН</b>\n\nВыбери, кому передать клан <b>{clan['name']}</b>:\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for m in others:
        clean = get_clean_name(m['user_id'])
        text += f"• {get_user_display_by_id(m['user_id'])}\n"
        markup.add(btn(clean, callback_data=f"clan_transfer_to_{clan_id}_{m['user_id']}", style='primary'))
    markup.add(btn("Отмена", callback_data=f"clan_back_{clan_id}", style='danger'))
    safe_edit(call.message.chat.id, call.message.message_id, text, parse_mode='HTML', reply_markup=markup)
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_transfer_to_"))
def clan_transfer_to(call):
    parts = call.data.split("_")
    clan_id = int(parts[3])
    new_leader = int(parts[4])
    clan = get_clan_by_id(clan_id)
    if not clan:
        safe_answer(call.id, "❌", show_alert=True)
        return
    if call.from_user.id != clan['leader_id']:
        safe_answer(call.id, "❌ Только лидер", show_alert=True)
        return
    members = [m['user_id'] for m in get_clan_members(clan_id)]
    if new_leader not in members:
        safe_answer(call.id, "❌ Он не в клане", show_alert=True)
        return
    transfer_clan(clan_id, new_leader)
    safe_answer(call.id, "✅ Клан передан", show_alert=True)
    try:
        bot.send_message(new_leader, f"👑 Тебе передали клан {render_clan_name(clan)}!", parse_mode='HTML')
    except Exception:
        pass
    try:
        safe_edit(call.message.chat.id, call.message.message_id,
                  f"✅ Клан передан {get_user_display_by_id(new_leader)}.",
                  parse_mode='HTML')
    except Exception:
        pass


# ----- РАСПУСК -----

@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_disband_") and not call.data.startswith("clan_disband_ok_"))
def clan_disband_cb(call):
    try:
        clan_id = int(call.data.split("_")[2])
    except (ValueError, IndexError):
        safe_answer(call.id, "❌ Ошибка", show_alert=True)
        return
    clan = get_clan_by_id(clan_id)
    if not clan:
        safe_answer(call.id, "❌", show_alert=True)
        return
    if call.from_user.id != clan['leader_id']:
        safe_answer(call.id, "❌ Только лидер", show_alert=True)
        return
    emoji_prefix = ''
    if clan.get('emoji_id'):
        fallback = clan.get('emoji_fallback') or '🏰'
        emoji_prefix = f'<tg-emoji emoji-id="{clan["emoji_id"]}">{fallback}</tg-emoji>'
    members_count = get_clan_member_count(clan_id)
    text = (
        f"⚠️ <b>РАСПУСТИТЬ КЛАН?</b>\n\n"
        f"{emoji_prefix}<b>{clan['name']}</b> ({members_count}/{clan['max_members']})\n\n"
        f"<b>Это действие необратимо.</b>\n"
        f"Клан будет удалён, все участники выйдут."
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        btn("🔴 Да, распустить", callback_data=f"clan_disband_ok_{clan_id}", style='danger'),
        btn("🟢 Отмена", callback_data=f"clan_back_{clan_id}", style='success')
    )
    safe_edit(call.message.chat.id, call.message.message_id, text, parse_mode='HTML', reply_markup=markup)
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_disband_ok_"))
def clan_disband_ok(call):
    clan_id = int(call.data.split("_")[3])
    clan = get_clan_by_id(clan_id)
    if not clan:
        safe_answer(call.id, "❌", show_alert=True)
        return
    if call.from_user.id != clan['leader_id']:
        safe_answer(call.id, "❌ Только лидер", show_alert=True)
        return
    members = get_clan_members(clan_id)
    for m in members:
        try:
            bot.send_message(m['user_id'], f"⚠️ Клан {render_clan_name(clan)} распущен лидером.", parse_mode='HTML')
        except Exception:
            pass
    delete_clan(clan_id)
    safe_answer(call.id, "Клан распущен", show_alert=True)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass


# ----- ВЫХОД -----

@bot.callback_query_handler(func=lambda call: call.data.startswith("clan_leave_"))
def clan_leave_cb(call):
    clan_id = int(call.data.split("_")[2])
    clan = get_clan_by_id(clan_id)
    if not clan:
        safe_answer(call.id, "❌", show_alert=True)
        return
    user_clan = get_user_clan(call.from_user.id)
    if not user_clan or user_clan['id'] != clan_id:
        safe_answer(call.id, "❌ Ты не в этом клане", show_alert=True)
        return
    if call.from_user.id == clan['leader_id']:
        members = get_clan_members(clan_id)
        others = [m for m in members if m['user_id'] != clan['leader_id']]
        if others:
            text = f"👑 <b>Ты лидер клана</b>\n\nВыбери кому передать клан, или распусти:"
            markup = types.InlineKeyboardMarkup(row_width=1)
            for m in others:
                clean = get_clean_name(m['user_id'])
                markup.add(btn(f"Передать: {clean}", callback_data=f"clan_transfer_to_{clan_id}_{m['user_id']}", style='primary'))
            markup.add(btn("🗑 Распустить клан", callback_data=f"clan_disband_{clan_id}", style='danger'))
            markup.add(btn("Отмена", callback_data=f"clan_back_{clan_id}", style='success'))
            safe_edit(call.message.chat.id, call.message.message_id, text, parse_mode='HTML', reply_markup=markup)
            safe_answer(call.id)
            return
        else:
            delete_clan(clan_id)
            safe_answer(call.id, "Клан распущен (некому передать)", show_alert=True)
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            return
    remove_clan_member(call.from_user.id)
    safe_answer(call.id, "✅ Ты вышел из клана", show_alert=True)
    text, markup = build_my_clan_text(call.from_user.id)
    safe_edit(call.message.chat.id, call.message.message_id, text, parse_mode='HTML', reply_markup=markup)


# ---------- МОДЕРАЦИЯ ----------

def is_moderator(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM moderators WHERE user_id = %s', (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row is not None


def get_target_user(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user, message.reply_to_message.from_user.id
    parts = message.text.strip().split()
    if len(parts) > 1:
        username = parts[1].replace('@', '')
        if username:
            try:
                u = bot.get_chat(f"@{username}")
                if u.type == 'private':
                    return u, u.id
            except:
                pass
            try:
                uid = int(username)
                get_or_create_user(uid, "", "")
                return None, uid
            except:
                pass
    return None, None


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'бан')
def cmd_ban_user(message):
    if message.from_user.id != OWNER_ID:
        return
    _, tid = get_target_user(message)
    if not tid:
        safe_send(message.chat.id, f"{EMO_CANCEL} Укажите пользователя.", parse_mode='HTML')
        return
    if tid == OWNER_ID:
        safe_send(message.chat.id, f"{EMO_CANCEL} Владельца нельзя!", parse_mode='HTML')
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET banned = 1 WHERE user_id = %s', (tid,))
        conn.commit()
        cursor.close()
        conn.close()
    safe_send(message.chat.id, f"{EMO_SAFE} Пользователь {get_user_display_by_id(tid)} забанен.", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'разбан')
def cmd_unban_user(message):
    if message.from_user.id != OWNER_ID:
        return
    _, tid = get_target_user(message)
    if not tid:
        safe_send(message.chat.id, f"{EMO_CANCEL} Укажите пользователя.", parse_mode='HTML')
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET banned = 0 WHERE user_id = %s', (tid,))
        conn.commit()
        cursor.close()
        conn.close()
    safe_send(message.chat.id, f"{EMO_SAFE} Пользователь {get_user_display_by_id(tid)} разбанен.", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'кик')
def cmd_kick_user(message):
    if message.from_user.id != OWNER_ID:
        safe_send(message.chat.id, f"{EMO_CANCEL} Только владелец!", parse_mode='HTML')
        return
    if message.chat.type not in ['group', 'supergroup']:
        safe_send(message.chat.id, f"{EMO_CANCEL} Только в группах!", parse_mode='HTML')
        return
    _, tid = get_target_user(message)
    if not tid:
        safe_send(message.chat.id, f"{EMO_CANCEL} Укажите пользователя.", parse_mode='HTML')
        return
    if tid == OWNER_ID:
        safe_send(message.chat.id, f"{EMO_CANCEL} Владельца нельзя!", parse_mode='HTML')
        return
    try:
        bot.ban_chat_member(message.chat.id, tid)
        bot.unban_chat_member(message.chat.id, tid)
        safe_send(message.chat.id, f"👢 {get_user_display_by_id(tid)} кикнут!", parse_mode='HTML')
    except Exception as e:
        safe_send(message.chat.id, f"{EMO_CANCEL} Ошибка: {e}", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith('пополнить'))
def cmd_owner_add_balance(message):
    if message.from_user.id != OWNER_ID:
        safe_send(message.chat.id, f"{EMO_CANCEL} Только владелец!", parse_mode='HTML')
        return
    parts = message.text.strip().lower().split()
    if len(parts) < 2:
        safe_send(message.chat.id, f"{EMO_CANCEL} Формат: <code>пополнить [сумма]</code>", parse_mode='HTML')
        return
    try:
        amount = int(parts[1])
    except:
        safe_send(message.chat.id, f"{EMO_CANCEL} Сумма должна быть числом!", parse_mode='HTML')
        return
    if amount <= 0:
        safe_send(message.chat.id, f"{EMO_CANCEL} Сумма > 0!", parse_mode='HTML')
        return
    _, tid = get_target_user(message)
    if not tid:
        safe_send(message.chat.id, f"{EMO_CANCEL} Укажите пользователя.", parse_mode='HTML')
        return
    update_balance(tid, amount)
    safe_send(message.chat.id, f"{EMO_CROWN} Пополнил {get_user_display_by_id(tid)} на <b>{amount:,} ноксов {EMO_NOX}</b>!", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith('отжать'))
def cmd_withdraw_balance(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    if message.from_user.id != OWNER_ID:
        safe_send(message.chat.id, f"{EMO_CANCEL} Только владелец!", parse_mode='HTML')
        return
    parts = message.text.strip().lower().split()
    if len(parts) < 2:
        safe_send(message.chat.id, f"{EMO_CANCEL} Формат: <code>отжать [сумма]</code>", parse_mode='HTML')
        return
    try:
        amount = int(parts[1])
    except:
        safe_send(message.chat.id, f"{EMO_CANCEL} Сумма должна быть числом!", parse_mode='HTML')
        return
    if amount <= 0:
        safe_send(message.chat.id, f"{EMO_CANCEL} Сумма > 0!", parse_mode='HTML')
        return
    _, tid = get_target_user(message)
    if not tid:
        safe_send(message.chat.id, f"{EMO_CANCEL} Укажите пользователя.", parse_mode='HTML')
        return
    tu = get_or_create_user(tid, "", "")
    if tid == OWNER_ID:
        safe_send(message.chat.id, f"{EMO_CANCEL} Нельзя у владельца!", parse_mode='HTML')
        return
    if tu['balance'] < amount:
        safe_send(message.chat.id, f"{EMO_CANCEL} Мало ноксов!", parse_mode='HTML')
        return
    update_balance(tid, -amount)
    update_balance(OWNER_ID, amount)
    tf = get_or_create_user(tid, "", "")
    safe_send(message.chat.id, f"{EMO_CROWN} Снял <b>{amount:,} ноксов {EMO_NOX}</b>!\n📉 Остаток: <b>{tf['balance']:,}</b>\n{EMO_GOLDTEXT} Вам: <b>+{amount:,} ноксов {EMO_NOX}</b>", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'модераторы')
def show_moderators(message):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, role FROM moderators ORDER BY CASE WHEN role = 'owner' THEN 0 ELSE 1 END")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    if not rows:
        safe_send(message.chat.id, f"{EMO_CANCEL} Пусто.", parse_mode='HTML')
        return
    text = f"{EMO_MODS} <b>МОДЕРАТОРЫ</b>\n\n"
    for row in rows:
        u = get_or_create_user(row['user_id'], "", "")
        icon = EMO_CROWN if row['role'] == 'owner' else "🛡️"
        role = "Владелец" if row['role'] == 'owner' else "Модератор"
        text += f"{icon} {role} — {get_user_display(u)}\n"
    safe_send(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('мут'))
def mute_user(message):
    try:
        if not is_moderator(message.from_user.id):
            safe_send(message.chat.id, f"{EMO_CANCEL} Нет прав!", parse_mode='HTML')
            return
        if message.chat.type not in ['group', 'supergroup']:
            safe_send(message.chat.id, f"{EMO_CANCEL} Только в группах!", parse_mode='HTML')
            return
        parts = message.text.split()
        if len(parts) < 2:
            safe_send(message.chat.id, f"{EMO_CANCEL} Формат: мут 1ч @user", parse_mode='HTML')
            return
        time_str = parts[1].lower()
        target_username = None
        for part in parts[2:]:
            if part.startswith('@'):
                target_username = part[1:]
                break
        if not target_username:
            if message.reply_to_message:
                target_id = message.reply_to_message.from_user.id
            else:
                safe_send(message.chat.id, f"{EMO_CANCEL} Укажите пользователя.", parse_mode='HTML')
                return
        else:
            try:
                cm = bot.get_chat_member(message.chat.id, f"@{target_username}")
                target_id = cm.user.id
            except:
                safe_send(message.chat.id, f"{EMO_CANCEL} Не найден.", parse_mode='HTML')
                return
        bcm = bot.get_chat_member(message.chat.id, get_bot_id())
        if not bcm.can_restrict_members:
            safe_send(message.chat.id, f"{EMO_CANCEL} Бот без прав.", parse_mode='HTML')
            return
        if target_id == OWNER_ID:
            safe_send(message.chat.id, f"{EMO_CANCEL} Владельца нельзя!", parse_mode='HTML')
            return
        if message.from_user.id != OWNER_ID and is_moderator(target_id):
            safe_send(message.chat.id, f"{EMO_CANCEL} Модератора нельзя!", parse_mode='HTML')
            return
        seconds = 0
        if time_str == 'навсегда':
            seconds = 315360000
        elif time_str.endswith('м'):
            seconds = int(time_str[:-1]) * 60
        elif time_str.endswith('ч'):
            seconds = int(time_str[:-1]) * 3600
        elif time_str.endswith('д'):
            seconds = int(time_str[:-1]) * 86400
        else:
            safe_send(message.chat.id, f"{EMO_CANCEL} Формат: 1ч, 30м, 1д, навсегда", parse_mode='HTML')
            return
        until = datetime.datetime.now(timezone.utc) + datetime.timedelta(seconds=seconds)
        perms = types.ChatPermissions(
            can_send_messages=False, can_send_media=False, can_send_other_messages=False,
            can_add_web_page_previews=False, can_send_polls=False, can_change_info=False,
            can_invite_users=False, can_pin_messages=False
        )
        bot.restrict_chat_member(message.chat.id, target_id, permissions=perms, until_date=until)
        dur = 'навсегда' if time_str == 'навсегда' else time_str
        who = "владельцем" if message.from_user.id == OWNER_ID else "модератором"
        safe_send(message.chat.id, f"{EMO_MUTE} {get_user_display_by_id(target_id)} замучен {who} на {dur}.", parse_mode='HTML')
    except Exception as e:
        safe_send(message.chat.id, f"{EMO_CANCEL} Ошибка: {e}", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'размут')
def unmute_user(message):
    try:
        if not is_moderator(message.from_user.id):
            safe_send(message.chat.id, f"{EMO_CANCEL} Нет прав!", parse_mode='HTML')
            return
        if message.chat.type not in ['group', 'supergroup']:
            safe_send(message.chat.id, f"{EMO_CANCEL} Только в группах!", parse_mode='HTML')
            return
        parts = message.text.split()
        target_username = None
        for part in parts[1:]:
            if part.startswith('@'):
                target_username = part[1:]
                break
        if not target_username:
            if message.reply_to_message:
                target_id = message.reply_to_message.from_user.id
            else:
                safe_send(message.chat.id, f"{EMO_CANCEL} Укажите пользователя.", parse_mode='HTML')
                return
        else:
            try:
                cm = bot.get_chat_member(message.chat.id, f"@{target_username}")
                target_id = cm.user.id
            except:
                safe_send(message.chat.id, f"{EMO_CANCEL} Не найден.", parse_mode='HTML')
                return
        perms = types.ChatPermissions(
            can_send_messages=True, can_send_media=True, can_send_other_messages=True,
            can_add_web_page_previews=True, can_send_polls=True, can_change_info=True,
            can_invite_users=True, can_pin_messages=True
        )
        bot.restrict_chat_member(message.chat.id, target_id, permissions=perms, until_date=None)
        safe_send(message.chat.id, f"{EMO_SAFE} {get_user_display_by_id(target_id)} размучен.", parse_mode='HTML')
    except Exception as e:
        safe_send(message.chat.id, f"{EMO_CANCEL} Ошибка: {e}", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.lower() == 'удалить')
def cmd_delete_message(message):
    try:
        if not is_moderator(message.from_user.id) and message.from_user.id != OWNER_ID:
            safe_send(message.chat.id, f"{EMO_CANCEL} Нет прав!", parse_mode='HTML')
            return
        if not message.reply_to_message:
            safe_send(message.chat.id, f"{EMO_CANCEL} Ответьте на сообщение.", parse_mode='HTML')
            return
        bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
    except Exception as e:
        safe_send(message.chat.id, f"{EMO_CANCEL} Ошибка: {e}", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('повысить'))
def cmd_promote_moderator(message):
    if message.from_user.id != OWNER_ID:
        return
    target, target_id = get_target_user(message)
    if not target_id or target_id == OWNER_ID:
        return
    if is_moderator(target_id):
        safe_send(message.chat.id, "Уже модератор.")
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO moderators (user_id, role, added_by) VALUES (%s, 'moderator', %s) ON CONFLICT (user_id) DO NOTHING",
            (target_id, OWNER_ID))
        conn.commit()
        cursor.close()
        conn.close()
    safe_send(message.chat.id, f"{EMO_SAFE} {get_user_display_by_id(target_id)} теперь модератор!", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('снять'))
def cmd_demote_moderator(message):
    if message.from_user.id != OWNER_ID:
        return
    target, target_id = get_target_user(message)
    if not target_id or target_id == OWNER_ID:
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM moderators WHERE user_id = %s AND role != 'owner'", (target_id,))
        conn.commit()
        cursor.close()
        conn.close()
    safe_send(message.chat.id, f"{EMO_SAFE} {get_user_display_by_id(target_id)} больше не модератор.", parse_mode='HTML')


# ---------- СЛОТЫ ----------

user_decks = {}


def get_next_result(user_id):
    if user_id not in user_decks or not user_decks[user_id]:
        deck = ['lose'] * 5000 + ['fruit'] * 4920 + ['diamond'] * 80
        random.shuffle(deck)
        user_decks[user_id] = deck
    return user_decks[user_id].pop()


def is_player_in_active_game(user_id):
    for chat_games in list(active_games.values()):
        for g in list(chat_games.values()):
            if g.get('p1_id') == user_id or g.get('p2_id') == user_id:
                return True
            if g.get('current_turn') == user_id:
                return True
            if g.get('chooser_id') == user_id or g.get('guesser_id') == user_id:
                return True
    return False


def check_player_in_game(user_id):
    if user_id not in player_in_game:
        return False
    if not is_player_in_active_game(user_id):
        player_in_game.discard(user_id)
        return False
    return True


def add_player_to_game(user_id):
    player_in_game.add(user_id)


def remove_player_from_game(user_id):
    player_in_game.discard(user_id)


def force_cleanup_player(user_id):
    for chat_id, chat_games in list(active_games.items()):
        for gid, g in list(chat_games.items()):
            if g.get('p1_id') == user_id or g.get('p2_id') == user_id or g.get('current_turn') == user_id \
                    or g.get('chooser_id') == user_id or g.get('guesser_id') == user_id:
                del active_games[chat_id][gid]
        if chat_id in active_games and not active_games[chat_id]:
            del active_games[chat_id]
    player_in_game.discard(user_id)


def finalize_game(chat_id, winner_id, loser_id, stake, game_type, result, msg_id=None):
    if result == 'win':
        wa = stake * 2
        update_balance(winner_id, wa)
        update_streak(winner_id, True, stake)
        update_streak(loser_id, False, stake)
        update_game_stats(winner_id, game_type, True)
        update_game_stats(loser_id, game_type, False)
        safe_send(chat_id, f"{EMO_CROWN} {get_user_display_by_id(winner_id)} +{wa - stake:,} ноксов {EMO_NOX}", parse_mode='HTML')
    elif result == 'draw':
        update_balance(winner_id, stake)
        update_balance(loser_id, stake)
        safe_send(chat_id, "🤝 Ничья! Ставки возвращены.")
    elif result == 'error':
        update_balance(winner_id, stake)
        update_balance(loser_id, stake)
        safe_send(chat_id, f"{EMO_CANCEL} Ошибка! Ставки возвращены.", parse_mode='HTML')
    else:
        return
    remove_player_from_game(winner_id)
    remove_player_from_game(loser_id)
    if chat_id in active_games and msg_id in active_games[chat_id]:
        del active_games[chat_id][msg_id]
        if not active_games[chat_id]:
            del active_games[chat_id]


@bot.callback_query_handler(func=lambda call: call.data == "reset_solo_games")
def reset_solo_games(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    refund = 0
    if user_id in solo_game_stakes:
        refund = solo_game_stakes.pop(user_id)
        try:
            update_balance(user_id, refund)
        except Exception as e:
            print(f"[RESET REFUND ERR] {e}")
    casino_in_progress[user_id] = False
    if user_id in chest_cache:
        del chest_cache[user_id]
    if refund > 0:
        safe_answer(call.id, f"✅ Ставка {refund:,} возвращена!", show_alert=True)
        try:
            safe_edit(chat_id, call.message.message_id,
                      f"{EMO_SAFE} <b>Активные соло-игры сброшены.</b>\n{EMO_NOX} Возврат ставки: <code>{refund:,}</code> ноксов",
                      parse_mode='HTML')
        except Exception:
            pass
    else:
        safe_answer(call.id, "✅ Активные соло-игры сброшены!", show_alert=True)
        try:
            safe_edit(chat_id, call.message.message_id,
                      f"{EMO_SAFE} Активные соло-игры сброшены. Можешь начинать заново!",
                      parse_mode='HTML')
        except Exception:
            pass


@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('слот'))
def cmd_slots_chat(message):
    if check_pm_game(message):
        return
    user_id = message.from_user.id
    chat_id = message.chat.id
    if casino_in_progress.get(user_id, False):
        markup = types.InlineKeyboardMarkup()
        markup.add(btn("Сбросить активные игры", callback_data="reset_solo_games", style='primary'))
        safe_send(chat_id, f"{EMO_TIMER} У вас уже есть активная игра!", reply_markup=markup, parse_mode='HTML')
        return
    match = re.match(r'^слот\s+(\S+)$', message.text.strip().lower())
    if not match:
        safe_send(chat_id, f"{EMO_BULB} Формат: <code>слот [ставка]</code>", parse_mode='HTML')
        return
    user = get_or_create_user(user_id, message.from_user.username, message.from_user.first_name)
    stake_arg = match.group(1).strip()
    if stake_arg == 'вб':
        stake = user['balance']
        if stake < 1:
            safe_send(chat_id, f"{EMO_BULB} У тебя нет ноксов {EMO_NOX}!", parse_mode='HTML')
            return
    else:
        try:
            stake = int(stake_arg)
        except ValueError:
            safe_send(chat_id, f"{EMO_BULB} Ставка должна быть числом или <code>вб</code>", parse_mode='HTML')
            return
        if stake < 1:
            safe_send(chat_id, f"{EMO_BULB} Ставка должна быть больше 0!", parse_mode='HTML')
            return
    if user['balance'] < stake:
        safe_send(chat_id, f"{EMO_BULB} Недостаточно баланса! Нужно <b>{stake:,}</b>, у тебя <b>{user['balance']:,}</b> ноксов {EMO_NOX}", parse_mode='HTML')
        return
    update_balance(user_id, -stake)
    try:
        emojis = ['🍒', '🍋', '🍊', '💎']
        result_type = get_next_result(user_id)
        if result_type == 'diamond':
            result = ['💎', '💎', '💎', '💎']
            win_multiplier = 10
        elif result_type == 'fruit':
            fruit = random.choice(['🍒', '🍋', '🍊'])
            result = [fruit] * 4
            win_multiplier = 2
        else:
            while True:
                result = [random.choice(emojis) for _ in range(4)]
                if not (all(e == result[0] for e in result) or all(e == '💎' for e in result)):
                    break
            win_multiplier = 0
        result_display = ' | '.join(SLOT_EMOJI_MAP[e] for e in result)
        if win_multiplier > 0:
            win_amount = stake * win_multiplier
            update_balance(user_id, win_amount)
            caption = f"{EMO_SLOTS} [ {result_display} ]\n+<b>{win_amount:,}</b> ноксов {EMO_NOX}! (x{win_multiplier})"
        else:
            caption = f"{EMO_SLOTS} [ {result_display} ]\n-<b>{stake:,}</b> ноксов {EMO_NOX}"
        safe_send(chat_id, caption, parse_mode='HTML')
    except Exception as e:
        print(f"[SLOTS ERROR] {e}")
        try:
            update_balance(user_id, stake)
        except:
            pass


# ---------- СУНДУК ----------

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('сундук'))
def cmd_chest(message):
    if check_pm_game(message):
        return
    user_id = message.from_user.id
    chat_id = message.chat.id
    if casino_in_progress.get(user_id, False):
        markup = types.InlineKeyboardMarkup()
        markup.add(btn("Сбросить активные игры", callback_data="reset_solo_games", style='primary'))
        safe_send(chat_id, f"{EMO_TIMER} У вас уже есть активная игра!", reply_markup=markup, parse_mode='HTML')
        return
    match = re.match(r'^сундук\s+(\S+)$', message.text.strip().lower())
    if not match:
        safe_send(chat_id, f"{EMO_BULB} Формат: <code>сундук [ставка]</code>", parse_mode="HTML")
        return
    user = get_or_create_user(user_id, message.from_user.username, message.from_user.first_name)
    stake_arg = match.group(1).strip()
    if stake_arg == 'вб':
        stake = user['balance']
        if stake < 1:
            safe_send(chat_id, f"{EMO_BULB} У тебя нет ноксов {EMO_NOX}!", parse_mode='HTML')
            return
    else:
        try:
            stake = int(stake_arg)
        except ValueError:
            safe_send(chat_id, f"{EMO_BULB} Ставка должна быть числом или <code>вб</code>", parse_mode='HTML')
            return
        if stake <= 0:
            safe_send(chat_id, f"{EMO_BULB} Ставка должна быть больше 0!", parse_mode='HTML')
            return
    if user['balance'] < stake:
        safe_send(chat_id, f"{EMO_BULB} Недостаточно баланса! Нужно <b>{stake:,}</b>, у тебя <b>{user['balance']:,}</b> ноксов {EMO_NOX}", parse_mode='HTML')
        return
    update_balance(user_id, -stake)
    casino_in_progress[user_id] = True
    solo_game_stakes[user_id] = stake
    chest_data = {
        'items': ['🔒', '🔒', '🔒', '🔒'],
        'real': ['💀', '💀', '💰', '💰'],
        'stake': stake,
        'golds': 0,
        'gold_indices': [],
        'finished': False,
        'taken': False
    }
    random.shuffle(chest_data['real'])
    chest_cache[user_id] = chest_data
    show_chest_game(chat_id, user_id, is_new=True)


def show_chest_game(chat_id, user_id, msg_id=None, is_new=False):
    data = chest_cache.get(user_id)
    if not data:
        return
    items = data['items']
    stake = data['stake']
    golds = data['golds']
    finished = data.get('finished', False)
    gold_indices = data.get('gold_indices', [])
    markup = types.InlineKeyboardMarkup(row_width=4)

    def gold_icon(idx):
        if idx in gold_indices:
            num = gold_indices.index(idx)
            return ICO_GOLD if num == 0 else ICO_GOLD2
        return ICO_GOLD

    row_btns = []
    for i in range(len(items)):
        if finished:
            real_item = data['real'][i]
            if real_item == '💰':
                row_btns.append(btn(' ', callback_data="ignore", icon=gold_icon(i)))
            elif real_item == '💀':
                row_btns.append(btn(' ', callback_data="ignore", icon=ICO_SKULL))
            else:
                row_btns.append(btn(' ', callback_data="ignore", icon=ICO_LOCK))
        else:
            if items[i] == '💰':
                row_btns.append(btn(' ', callback_data="ignore", icon=gold_icon(i)))
            elif items[i] == '💀':
                row_btns.append(btn(' ', callback_data="ignore", icon=ICO_SKULL))
            else:
                row_btns.append(btn(f"{i+1}", callback_data=f"chest_{i}", style='primary', icon=ICO_CHEST))
    markup.add(*row_btns)
    if golds > 0 and not finished and not data.get('taken', False):
        markup.add(btn("ЗАБРАТЬ", callback_data="chest_take", style='success', icon=ICO_GOLD_BTN))
    if finished:
        if data.get('win', False):
            wa = data.get('win_amount', 0)
            mult = data.get('multiplier', 1.5)
            text = f"🎉 <b>ВЫИГРЫШ!</b> +{wa:,} ноксов {EMO_NOX} (x{mult})"
        else:
            text = f"{EMO_SKULL} <b>ПРОИГРЫШ!</b> -{stake:,} ноксов {EMO_NOX}"
    else:
        if golds == 0:
            text = f"{EMO_CHEST} <b>ВЫБЕРИ СУНДУК</b>\n{EMO_NOX} Ставка: {stake:,}"
        elif golds == 1:
            win = int(stake * 1.5)
            text = f"{EMO_GOLD} <b>ЗОЛОТО!</b> {win:,} (x1.5)\nВыбери ещё или забери"
        else:
            text = f"{EMO_CHEST} <b>ВЫБЕРИ СУНДУК</b>\n{EMO_NOX} Ставка: {stake:,}"
    if is_new:
        safe_send(chat_id, text, parse_mode='HTML', reply_markup=markup)
    else:
        safe_edit(chat_id, msg_id, text, parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("chest_") and not call.data.startswith("chest_take"))
def chest_choice(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = chest_cache.get(user_id)
    if not data or data.get('finished', False) or not casino_in_progress.get(user_id, False):
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
                show_chest_game(chat_id, user_id, msg_id)
                return
            elif data['golds'] == 2:
                wa = int(stake * 2)
                update_balance(user_id, wa)
                data['finished'] = True
                data['win'] = True
                data['win_amount'] = wa
                data['multiplier'] = 2
                casino_in_progress[user_id] = False
                safe_answer(call.id, "🎉 ДЖЕКПОТ x2!")
                show_chest_game(chat_id, user_id, msg_id)
                clean_chest(user_id)
                return
        else:
            items[idx] = '💀'
            data['finished'] = True
            data['win'] = False
            casino_in_progress[user_id] = False
            safe_answer(call.id, "💀 Проигрыш!")
            show_chest_game(chat_id, user_id, msg_id)
            clean_chest(user_id)
            return
    except Exception:
        safe_answer(call.id, "❌", show_alert=True)
        clean_chest(user_id)


@bot.callback_query_handler(func=lambda call: call.data == "chest_take")
def chest_take(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = chest_cache.get(user_id)
    if not data or data.get('finished', False) or data.get('taken', False):
        safe_answer(call.id, "⏳", show_alert=True)
        return
    try:
        stake = data['stake']
        win = int(stake * 1.5)
        update_balance(user_id, win)
        data['finished'] = True
        data['win'] = True
        data['win_amount'] = win
        data['multiplier'] = 1.5
        data['taken'] = True
        casino_in_progress[user_id] = False
        safe_answer(call.id, f"✅ +{win:,}!")
        show_chest_game(chat_id, user_id, msg_id)
        clean_chest(user_id)
    except Exception:
        safe_answer(call.id, "❌ Ошибка", show_alert=True)
        clean_chest(user_id)


def clean_chest(user_id):
    if user_id in chest_cache:
        del chest_cache[user_id]
    casino_in_progress[user_id] = False
    solo_game_stakes.pop(user_id, None)


# ---------- ЭТАЖИ ----------

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('этажи'))
def cmd_floors_game(message):
    if check_pm_game(message):
        return
    user_id = message.from_user.id
    chat_id = message.chat.id
    if casino_in_progress.get(user_id, False):
        markup = types.InlineKeyboardMarkup()
        markup.add(btn("Сбросить активные игры", callback_data="reset_solo_games", style='primary'))
        safe_send(chat_id, f"{EMO_TIMER} У вас уже есть активная игра!", reply_markup=markup, parse_mode='HTML')
        return
    match = re.match(r'^этажи\s+(\S+)$', message.text.strip().lower())
    if not match:
        safe_send(chat_id, f"{EMO_BULB} Формат: <code>этажи [ставка]</code>", parse_mode='HTML')
        return
    user = get_or_create_user(user_id, message.from_user.username, message.from_user.first_name)
    stake_arg = match.group(1).strip()
    if stake_arg == 'вб':
        stake = user['balance']
        if stake < 1:
            safe_send(chat_id, f"{EMO_BULB} Нет {EMO_NOX}!", parse_mode='HTML')
            return
    else:
        try:
            stake = int(stake_arg)
        except ValueError:
            safe_send(chat_id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
        if stake < 1:
            safe_send(chat_id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
            return
    if user['balance'] < stake:
        safe_send(chat_id, f"{EMO_BULB} Недостаточно баланса! Нужно <b>{stake:,}</b>, у тебя <b>{user['balance']:,}</b> ноксов {EMO_NOX}", parse_mode='HTML')
        return
    update_balance(user_id, -stake)
    casino_in_progress[user_id] = True
    solo_game_stakes[user_id] = stake
    floor_data = {
        'user_id': user_id,
        'stake': stake,
        'floor': 1,
        'multiplier': 1.0,
        'finished': False,
        'chat_id': chat_id,
        'msg_id': None
    }
    show_floor_game(chat_id, floor_data, is_new=True)


def show_floor_game(chat_id, floor_data, msg_id=None, is_new=False):
    user_id = floor_data['user_id']
    floor = floor_data['floor']
    multiplier = floor_data['multiplier']
    stake = floor_data['stake']
    if floor_data.get('finished', False):
        return
    potential_win = int(stake * multiplier)
    text = f"{EMO_FLOOR} ЭТАЖ {floor}\n{EMO_NOX} Ставка: {stake:,}\n{EMO_MULT} Множитель: x{multiplier}\n{EMO_TROPHY} Потенциальный выигрыш: {potential_win:,}"
    markup = types.InlineKeyboardMarkup(row_width=2)
    if floor >= 10:
        markup.add(btn("ЗАБРАТЬ", callback_data=f"floors_take_{user_id}_{floor}_{stake}_{multiplier}", style='success', icon=ICO_GOLD_BTN))
    else:
        markup.add(btn("ПОДНЯТЬСЯ", callback_data=f"floors_up_{user_id}_{floor}_{stake}_{multiplier}", style='primary', icon=ICO_BULB))
        markup.add(btn("ЗАБРАТЬ", callback_data=f"floors_take_{user_id}_{floor}_{stake}_{multiplier}", style='success', icon=ICO_GOLD_BTN))
    if is_new:
        msg = safe_send(chat_id, text, parse_mode='HTML', reply_markup=markup)
        if msg:
            floor_data['msg_id'] = msg.message_id
    elif msg_id:
        safe_edit(chat_id, msg_id, text, parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("floors_up_"))
def floors_up(call):
    parts = call.data.split("_")
    user_id = int(parts[2])
    floor = int(parts[3])
    stake = int(parts[4])
    multiplier = float(parts[5])
    if call.from_user.id != user_id:
        safe_answer(call.id, "🖕 Это не твоя игра, додик!", show_alert=True)
        return
    lose_chances = {1:15, 2:20, 3:25, 4:30, 5:35, 6:45, 7:55, 8:70, 9:85}
    if random.randint(1, 100) <= lose_chances.get(floor, 0):
        casino_in_progress[user_id] = False
        solo_game_stakes.pop(user_id, None)
        safe_edit(call.message.chat.id, call.message.message_id,
                  f"{EMO_SKULL} БАХ! Упал!\nСтавка {stake:,} ноксов {EMO_NOX} сгорела!", parse_mode='HTML')
        safe_answer(call.id, "💀!")
    else:
        nf = floor + 1
        mults = {2:1.2, 3:1.4, 4:1.7, 5:2.0, 6:2.5, 7:3.0, 8:4.0, 9:5.0, 10:10.0}
        nm = mults.get(nf, multiplier)
        fd = {'user_id': user_id, 'stake': stake, 'floor': nf, 'multiplier': nm, 'finished': False,
              'chat_id': call.message.chat.id, 'msg_id': call.message.message_id}
        show_floor_game(call.message.chat.id, fd, call.message.message_id)
        safe_answer(call.id, "⬆️!")


@bot.callback_query_handler(func=lambda call: call.data.startswith("floors_take_"))
def floors_take(call):
    parts = call.data.split("_")
    user_id = int(parts[2])
    stake = int(parts[4])
    multiplier = float(parts[5])
    if call.from_user.id != user_id:
        safe_answer(call.id, "🖕 Это не твоя игра, додик!", show_alert=True)
        return
    wa = int(stake * multiplier)
    update_balance(user_id, wa)
    casino_in_progress[user_id] = False
    solo_game_stakes.pop(user_id, None)
    safe_edit(call.message.chat.id, call.message.message_id,
              f"{EMO_GOLDTEXT} ЗАБРАЛ!\n+{wa:,} ноксов {EMO_NOX}! (x{multiplier})", parse_mode='HTML')
    safe_answer(call.id, f"✅ +{wa}!")


# ---------- РУЛЕТКА ----------

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith('рулетка'))
def cmd_roulette_game(message):
    if check_pm_game(message):
        return
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id, sender_chat=message.sender_chat):
        return
    match = re.match(r'^рулетка\s+(\S+)$', message.text.strip().lower())
    if not match:
        safe_send(message.chat.id, f"{EMO_BULB} Формат: <code>рулетка [ставка]</code>", parse_mode='HTML')
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    stake_arg = match.group(1).strip()
    if stake_arg == 'вб':
        stake = user['balance']
        if stake < 1:
            safe_send(message.chat.id, f"{EMO_BULB} Нет {EMO_NOX}!", parse_mode='HTML')
            return
    else:
        try:
            stake = int(stake_arg)
        except ValueError:
            safe_send(message.chat.id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
        if stake < 1:
            safe_send(message.chat.id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
            return
    if user['balance'] < stake:
        safe_send(message.chat.id, f"{EMO_BULB} Недостаточно баланса! Нужно <b>{stake:,}</b>, у тебя <b>{user['balance']:,}</b> ноксов {EMO_NOX}", parse_mode='HTML')
        return
    if check_player_in_game(message.from_user.id):
        force_cleanup_player(message.from_user.id)
    user_display = get_user_display(user)
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target = get_or_create_user(target_id, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
        target_display = get_user_display(target)
        if target_id == user['user_id']:
            safe_send(message.chat.id, f"{EMO_BULB} С собой нельзя!", parse_mode='HTML')
            return
        if target['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} У соперника мало баланса! Нужно <b>{stake:,}</b>, у него <b>{target['balance']:,}</b> {EMO_NOX}", parse_mode='HTML')
            return
        if check_player_in_game(target_id):
            safe_send(message.chat.id, f"{EMO_BULB} Соперник уже в игре!", parse_mode='HTML')
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_roulette_{message.from_user.id}_{target_id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT))
        markup.add(btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_ROULETTE} {user_display} вызывает {target_display}!\n{EMO_SOLO_HEADER} Игра: Русская рулетка\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'roulette', 'stake': stake, 'chat_id': message.chat.id}
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять вызов", callback_data=f"join_roulette_open_{message.from_user.id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT))
        markup.add(btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_ROULETTE} {user_display} ищет соперника!\n{EMO_SOLO_HEADER} Игра: Русская рулетка\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'roulette', 'stake': stake, 'chat_id': message.chat.id}


def start_roulette_match(chat_id, p1, p2, stake):
    add_player_to_game(p1['user_id'])
    add_player_to_game(p2['user_id'])
    ct = random.choice([p1['user_id'], p2['user_id']])
    p1d = get_user_display(p1)
    p2d = get_user_display(p2)
    gd = {'p1_id': p1['user_id'], 'p2_id': p2['user_id'], 'stake': stake, 'current_turn': ct,
          'shot_count': 0, 'finished': False, 'chat_id': chat_id}
    msg = safe_send(chat_id, f"{EMO_ROULETTE} РУЛЕТКА!\n{p1d} {EMO_VS} {p2d}\n{EMO_NOX} {stake:,}\nХодит: {get_user_display_by_id(ct)}", parse_mode='HTML')
    if not msg:
        return
    gmid = msg.message_id
    active_games[chat_id] = active_games.get(chat_id, {})
    active_games[chat_id][gmid] = gd
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("ВЫСТРЕЛИТЬ", callback_data=f"roulette_shoot_{gmid}_{ct}", style='danger', icon=ICO_ROULETTE))
    safe_edit(chat_id, gmid, f"{EMO_ROULETTE} РУЛЕТКА!\n{p1d} {EMO_VS} {p2d}\n{EMO_NOX} {stake:,}\nХодит: {get_user_display_by_id(ct)}", reply_markup=markup, parse_mode='HTML')
    start_timer(chat_id, gmid, game_type='roulette', timeout=60)


@bot.callback_query_handler(func=lambda call: call.data.startswith("roulette_shoot_"))
def roulette_shoot(call):
    parts = call.data.split("_")
    gmid = int(parts[2])
    tid = int(parts[3])
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
        safe_edit(cid, gmid, f"💥 БАХ! {get_user_display_by_id(lid)} проиграл!\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,} ноксов {EMO_NOX}!", parse_mode='HTML')
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
        safe_edit(cid, gmid, f"{EMO_ROULETTE}\n{EMO_NOX} {g['stake']:,}\nВыстрел {g['shot_count']}\nХодит: {nd}", reply_markup=markup, parse_mode='HTML')
        start_timer(cid, gmid, game_type='roulette', timeout=60)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_roulette_open_"))
def join_roulette_open(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    parts = call.data.split("_")
    hid = int(parts[3])
    stake = int(parts[4])
    mid = int(parts[5])
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
        safe_answer(call.id, "❌ Недостаточно баланса!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    start_roulette_match(call.message.chat.id, h, gu, stake)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_roulette_"))
def join_roulette(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    parts = call.data.split("_")
    hid = int(parts[2])
    tid = int(parts[3])
    stake = int(parts[4])
    mid = int(parts[5])
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
        safe_answer(call.id, "❌ Недостаточно баланса!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    start_roulette_match(call.message.chat.id, h, gu, stake)


# ---------- ОРЁЛ/РЕШКА ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith(('орел', 'орёл', 'решка')))
def cmd_eagle_game(message):
    if check_pm_game(message):
        return
    try:
        if check_banned(message.from_user.id, message.chat.id):
            return
        if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id, sender_chat=message.sender_chat):
            return
        match = re.match(r'^(орел|орёл|решка)\s+(\S+)$', message.text.strip().lower())
        if not match:
            safe_send(message.chat.id, f"{EMO_BULB} Формат: <code>орел [ставка]</code>", parse_mode='HTML')
            return
        user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        stake_arg = match.group(2).strip()
        if stake_arg == 'вб':
            stake = user['balance']
            if stake < 1:
                safe_send(message.chat.id, f"{EMO_BULB} Нет {EMO_NOX}!", parse_mode='HTML')
                return
        else:
            try:
                stake = int(stake_arg)
            except ValueError:
                safe_send(message.chat.id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
                return
            if stake < 1:
                safe_send(message.chat.id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
                return
        if user['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} Недостаточно баланса! Нужно <b>{stake:,}</b>, у тебя <b>{user['balance']:,}</b> ноксов {EMO_NOX}", parse_mode='HTML')
            return
        if check_player_in_game(message.from_user.id):
            force_cleanup_player(message.from_user.id)
        user_display = get_user_display(user)
        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            target = get_or_create_user(target_id, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
            target_display = get_user_display(target)
            if target_id == user['user_id']:
                safe_send(message.chat.id, f"{EMO_BULB} С собой нельзя!", parse_mode='HTML')
                return
            if target['balance'] < stake:
                safe_send(message.chat.id, f"{EMO_BULB} У соперника мало баланса! Нужно <b>{stake:,}</b>, у него <b>{target['balance']:,}</b> {EMO_NOX}", parse_mode='HTML')
                return
            if check_player_in_game(target_id):
                safe_send(message.chat.id, f"{EMO_BULB} Соперник уже в игре!", parse_mode='HTML')
                return
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                btn("Принять", callback_data=f"join_eg_dir:{user['user_id']}:{target_id}:{stake}", style='success', icon=ICO_ACCEPT),
                btn("Отмена", callback_data=f"cancel_eg:{user['user_id']}", style='danger', icon=ICO_CANCEL)
            )
            msg = safe_send(message.chat.id, f"{EMO_EAGLE} {user_display} вызывает {target_display}!\n{EMO_SOLO_HEADER} Игра: Орёл/Решка\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
        else:
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                btn("Принять", callback_data=f"join_eg_open:{user['user_id']}:{stake}", style='success', icon=ICO_ACCEPT),
                btn("Отмена", callback_data=f"cancel_eg:{user['user_id']}", style='danger', icon=ICO_CANCEL)
            )
            msg = safe_send(message.chat.id, f"{EMO_EAGLE} {user_display} ищет соперника!\n{EMO_SOLO_HEADER} Игра: Орёл/Решка\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
        if msg:
            with invite_lock:
                invites[msg.message_id] = {'host_id': user['user_id'], 'game_type': 'eagle', 'stake': stake, 'chat_id': message.chat.id}
    except Exception as e:
        safe_send(message.chat.id, f"❌ Ошибка: {e}", parse_mode='HTML')


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
        if call.message.message_id in invites:
            del invites[call.message.message_id]
    start_eagle_duel(call, hid, tid, st)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_eg_open:"))
def join_eagle_open(call):
    safe_answer(call.id)
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    _, hid, st = call.data.split(":")
    hid, st = int(hid), int(st)
    if call.from_user.id == hid:
        safe_send(call.message.chat.id, "❌ С собой!", parse_mode='HTML')
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
        if call.message.message_id in invites:
            del invites[call.message.message_id]
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass


def start_eagle_duel(call, hid, gid, stake):
    h = get_or_create_user(hid, "", "")
    g = get_or_create_user(gid, call.from_user.username, call.from_user.first_name)
    if h['balance'] < stake or g['balance'] < stake:
        safe_send(call.message.chat.id, "❌ Недостаточно баланса!", parse_mode='HTML')
        return
    if check_player_in_game(hid):
        force_cleanup_player(hid)
    if check_player_in_game(gid):
        force_cleanup_player(gid)
    if random.random() < 0.5:
        cid, gsi = hid, gid
    else:
        cid, gsi = gid, hid
    cd = get_user_display_by_id(cid)
    gd = get_user_display_by_id(gsi)
    update_balance(hid, -stake)
    update_balance(gid, -stake)
    add_player_to_game(cid)
    add_player_to_game(gsi)
    game_id = f"e{int(time.time())}{random.randint(100,999)}"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        btn("Орёл", callback_data=f"egch:{game_id}:1", style='primary', icon=ICO_EAGLE),
        btn("Решка", callback_data=f"egch:{game_id}:2", style='success', icon=ICO_EAGLE)
    )
    safe_edit(call.message.chat.id, call.message.message_id,
              f"{EMO_EAGLE} Орёл/Решка!\n{EMO_NOX} {stake:,}\n🎯 {cd} ВЫБИРАЕТ\n🤔 {gd} УГАДЫВАЕТ",
              parse_mode='HTML', reply_markup=markup)
    if call.message.chat.id not in active_games:
        active_games[call.message.chat.id] = {}
    active_games[call.message.chat.id][game_id] = {
        'game_type': 'eagle', 'chooser_id': cid, 'guesser_id': gsi, 'stake': stake,
        'state': 'choose', 'msg_id': call.message.message_id, 'finished': False
    }
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
    cd = get_user_display_by_id(g['chooser_id'])
    gd = get_user_display_by_id(g['guesser_id'])
    ggid = f"e{int(time.time())}{random.randint(100,999)}"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        btn("Орёл", callback_data=f"eggs:{ggid}:1", style='primary', icon=ICO_EAGLE),
        btn("Решка", callback_data=f"eggs:{ggid}:2", style='success', icon=ICO_EAGLE)
    )
    safe_edit(cid, g['msg_id'], f"{EMO_EAGLE} {cd} загадал!\n🤔 {gd} угадай!", parse_mode='HTML', reply_markup=markup)
    c_id, gs_id, st, mid = g['chooser_id'], g['guesser_id'], g['stake'], g['msg_id']
    del active_games[cid][gid]
    active_games[cid][ggid] = {
        'game_type': 'eagle_guess', 'chooser_id': c_id, 'guesser_id': gs_id,
        'stake': st, 'choice': ch, 'msg_id': mid, 'finished': False
    }
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
    safe_edit(cid, g['msg_id'], f"{EMO_EAGLE} <b>РЕЗУЛЬТАТ:</b>\n\n{txt}\n\n{EMO_CROWN} {get_user_display_by_id(wid)} +{st:,} ноксов {EMO_NOX}!", parse_mode='HTML', reply_markup=None)
    remove_player_from_game(wid)
    remove_player_from_game(lid)
    if cid in active_games and gid in active_games[cid]:
        del active_games[cid][gid]


# ---------- КОСТИ ----------

@bot.message_handler(func=lambda m: m.text and (m.text.strip().lower().startswith('кости') or m.text.strip().lower().startswith('кубики')))
def cmd_dice_game(message):
    if check_pm_game(message):
        return
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id, sender_chat=message.sender_chat):
        return
    match = re.match(r'^(кости|кубики)\s+(\S+)$', message.text.strip().lower())
    if not match:
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    stake_arg = match.group(2).strip()
    if stake_arg == 'вб':
        stake = user['balance']
        if stake < 1:
            safe_send(message.chat.id, f"{EMO_BULB} Нет {EMO_NOX}!", parse_mode='HTML')
            return
    else:
        try:
            stake = int(stake_arg)
        except ValueError:
            safe_send(message.chat.id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
        if stake < 1:
            safe_send(message.chat.id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
            return
    if user['balance'] < stake:
        safe_send(message.chat.id, f"{EMO_BULB} Недостаточно баланса! Нужно <b>{stake:,}</b>, у тебя <b>{user['balance']:,}</b> ноксов {EMO_NOX}", parse_mode='HTML')
        return
    if check_player_in_game(message.from_user.id):
        force_cleanup_player(message.from_user.id)
    user_display = get_user_display(user)
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target = get_or_create_user(target_id, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
        target_display = get_user_display(target)
        if target_id == user['user_id']:
            safe_send(message.chat.id, f"{EMO_BULB} С собой нельзя!", parse_mode='HTML')
            return
        if target['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} У соперника мало баланса! Нужно <b>{stake:,}</b>, у него <b>{target['balance']:,}</b> {EMO_NOX}", parse_mode='HTML')
            return
        if check_player_in_game(target_id):
            safe_send(message.chat.id, f"{EMO_BULB} Соперник уже в игре!", parse_mode='HTML')
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_dice_{message.from_user.id}_{target_id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT))
        markup.add(btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_DICE} {user_display} вызывает {target_display}!\n{EMO_SOLO_HEADER} Игра: Кости 1на1\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'dice', 'stake': stake, 'chat_id': message.chat.id}
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_dice_open_{message.from_user.id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT))
        markup.add(btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_DICE} {user_display} ищет соперника!\n{EMO_SOLO_HEADER} Игра: Кости 1на1\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'dice', 'stake': stake, 'chat_id': message.chat.id}


def run_dice_match_thread(cid, p1, p2, stake, mid):
    try:
        p1d = get_user_display(p1)
        p2d = get_user_display(p2)
        safe_send(cid, f"{p1d} бросает...", parse_mode='HTML')
        try:
            d1 = bot.send_dice(cid).dice.value
        except:
            finalize_game(cid, p1['user_id'], p2['user_id'], stake, 'dice', 'error', mid)
            return
        time.sleep(3)
        safe_send(cid, f"{p2d} бросает...", parse_mode='HTML')
        try:
            d2 = bot.send_dice(cid).dice.value
        except:
            finalize_game(cid, p1['user_id'], p2['user_id'], stake, 'dice', 'error', mid)
            return
        time.sleep(2)
        if d1 > d2:
            finalize_game(cid, p1['user_id'], p2['user_id'], stake, 'dice', 'win', mid)
        elif d2 > d1:
            finalize_game(cid, p2['user_id'], p1['user_id'], stake, 'dice', 'win', mid)
        else:
            safe_send(cid, f"🤝 Ничья ({d1}:{d2})! Перекидываем...")
            time.sleep(2)
            run_dice_match_thread(cid, p1, p2, stake, mid)
    except:
        pass


def run_dice_match(cid, p1, p2, stake, mid):
    add_player_to_game(p1['user_id'])
    add_player_to_game(p2['user_id'])
    threading.Thread(target=run_dice_match_thread, args=(cid, p1, p2, stake, mid), daemon=True).start()


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_dice_open_"))
def join_dice_open(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    parts = call.data.split("_")
    hid = int(parts[3])
    stake = int(parts[4])
    mid = int(parts[5])
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
        safe_answer(call.id, "❌ Недостаточно баланса!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    run_dice_match(call.message.chat.id, h, gu, stake, mid)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_dice_"))
def join_dice(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    parts = call.data.split("_")
    hid = int(parts[2])
    tid = int(parts[3])
    stake = int(parts[4])
    mid = int(parts[5])
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
        safe_answer(call.id, "❌ Недостаточно баланса!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    run_dice_match(call.message.chat.id, h, gu, stake, mid)


# ---------- ЦУЕФА ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith('цуефа'))
def cmd_rps_game(message):
    if check_pm_game(message):
        return
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id, sender_chat=message.sender_chat):
        return
    match = re.match(r'^цуефа\s+(\S+)$', message.text.strip().lower())
    if not match:
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    stake_arg = match.group(1).strip()
    if stake_arg == 'вб':
        stake = user['balance']
        if stake < 1:
            safe_send(message.chat.id, f"{EMO_BULB} Нет {EMO_NOX}!", parse_mode='HTML')
            return
    else:
        try:
            stake = int(stake_arg)
        except ValueError:
            safe_send(message.chat.id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
        if stake < 1:
            safe_send(message.chat.id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
            return
    if user['balance'] < stake:
        safe_send(message.chat.id, f"{EMO_BULB} Недостаточно баланса! Нужно <b>{stake:,}</b>, у тебя <b>{user['balance']:,}</b> ноксов {EMO_NOX}", parse_mode='HTML')
        return
    if check_player_in_game(message.from_user.id):
        force_cleanup_player(message.from_user.id)
    user_display = get_user_display(user)
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target = get_or_create_user(target_id, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
        target_display = get_user_display(target)
        if target_id == user['user_id']:
            safe_send(message.chat.id, f"{EMO_BULB} С собой нельзя!", parse_mode='HTML')
            return
        if target['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} У соперника мало баланса! Нужно <b>{stake:,}</b>, у него <b>{target['balance']:,}</b> {EMO_NOX}", parse_mode='HTML')
            return
        if check_player_in_game(target_id):
            safe_send(message.chat.id, f"{EMO_BULB} Соперник уже в игре!", parse_mode='HTML')
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_rps_{message.from_user.id}_{target_id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT))
        markup.add(btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_ROCK} {user_display} вызывает {target_display}!\n{EMO_SOLO_HEADER} Игра: Камень-Ножницы-Бумага\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'rps', 'stake': stake, 'chat_id': message.chat.id}
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_rps_open_{message.from_user.id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT))
        markup.add(btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_ROCK} {user_display} ищет соперника!\n{EMO_SOLO_HEADER} Игра: Камень-Ножницы-Бумага\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'rps', 'stake': stake, 'chat_id': message.chat.id}


def start_rps_match(cid, p1, p2, stake):
    add_player_to_game(p1['user_id'])
    add_player_to_game(p2['user_id'])
    p1d = get_user_display(p1)
    p2d = get_user_display(p2)
    markup = types.InlineKeyboardMarkup(row_width=3)
    msg = safe_send(cid, "Сделайте ход!")
    if not msg:
        return
    markup.add(btn("Камень", callback_data=f"play_rps_{msg.message_id}_🪨", style='primary', icon=ICO_ROCK))
    markup.add(btn("Ножницы", callback_data=f"play_rps_{msg.message_id}_✂️", style='danger', icon=ICO_SCISSORS))
    markup.add(btn("Бумага", callback_data=f"play_rps_{msg.message_id}_📄", style='success', icon=ICO_PAPER))
    active_games[cid] = active_games.get(cid, {})
    active_games[cid][msg.message_id] = {
        'p1_id': p1['user_id'], 'p2_id': p2['user_id'],
        'p1_choice': None, 'p2_choice': None, 'stake': stake,
        'game_type': 'rps', 'finished': False, 'chat_id': cid, 'msg_id': msg.message_id
    }
    safe_edit(cid, msg.message_id, f"{p1d} {EMO_VS} {p2d}!\n{EMO_NOX} {stake:,}\n{EMO_TIMER} 60с!", reply_markup=markup, parse_mode='HTML')
    start_timer(cid, msg.message_id, game_type='rps', timeout=60)


def check_rps_result(cid, mid):
    g = active_games[cid][mid]
    if g.get('finished', False) or not (g['p1_choice'] and g['p2_choice']):
        return
    cancel_timer(cid, mid)
    c1, c2 = g['p1_choice'], g['p2_choice']
    rules = {"🪨": "✂️", "✂️": "📄", "📄": "🪨"}
    p1d = get_user_display_by_id(g['p1_id'])
    p2d = get_user_display_by_id(g['p2_id'])
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
        safe_edit(cid, mid, f"🤝 Ничья! {cd[c1]}", reply_markup=markup, parse_mode='HTML')
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
        except:
            pass
        safe_send(cid, f"🏁 {p1d}: {cd[c1]}\n🏁 {p2d}: {cd[c2]}\n\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,} ноксов {EMO_NOX}!", parse_mode='HTML')
        del active_games[cid][mid]
        remove_player_from_game(wid)
        remove_player_from_game(lid)


@bot.callback_query_handler(func=lambda call: call.data.startswith("play_rps_"))
def play_rps(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    parts = call.data.split("_")
    mid = int(parts[2])
    ch = parts[3]
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
    parts = call.data.split("_")
    hid = int(parts[3])
    stake = int(parts[4])
    mid = int(parts[5])
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
        safe_answer(call.id, "❌ Недостаточно баланса!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    start_rps_match(call.message.chat.id, h, gu, stake)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_rps_"))
def join_rps(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    parts = call.data.split("_")
    hid = int(parts[2])
    tid = int(parts[3])
    stake = int(parts[4])
    mid = int(parts[5])
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
        safe_answer(call.id, "❌ Недостаточно баланса!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    start_rps_match(call.message.chat.id, h, gu, stake)


# ---------- КРЕСТИКИ-НОЛИКИ ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith('крестики'))
def cmd_ttt_game(message):
    if check_pm_game(message):
        return
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id, sender_chat=message.sender_chat):
        return
    match = re.match(r'^крестики\s+(\S+)$', message.text.strip().lower())
    if not match:
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    stake_arg = match.group(1).strip()
    if stake_arg == 'вб':
        stake = user['balance']
        if stake < 1:
            safe_send(message.chat.id, f"{EMO_BULB} Нет {EMO_NOX}!", parse_mode='HTML')
            return
    else:
        try:
            stake = int(stake_arg)
        except ValueError:
            safe_send(message.chat.id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
        if stake < 1:
            safe_send(message.chat.id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
            return
    if user['balance'] < stake:
        safe_send(message.chat.id, f"{EMO_BULB} Недостаточно баланса! Нужно <b>{stake:,}</b>, у тебя <b>{user['balance']:,}</b> ноксов {EMO_NOX}", parse_mode='HTML')
        return
    if check_player_in_game(message.from_user.id):
        force_cleanup_player(message.from_user.id)
    user_display = get_user_display(user)
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target = get_or_create_user(target_id, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
        target_display = get_user_display(target)
        if target_id == user['user_id']:
            safe_send(message.chat.id, f"{EMO_BULB} С собой нельзя!", parse_mode='HTML')
            return
        if target['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} У соперника мало баланса! Нужно <b>{stake:,}</b>, у него <b>{target['balance']:,}</b> {EMO_NOX}", parse_mode='HTML')
            return
        if check_player_in_game(target_id):
            safe_send(message.chat.id, f"{EMO_BULB} Соперник уже в игре!", parse_mode='HTML')
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_ttt_{message.from_user.id}_{target_id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT))
        markup.add(btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_TTT_X} {user_display} вызывает {target_display}!\n{EMO_TTT_INVITE} Игра: Крестики-Нолики 3х3\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'ttt', 'stake': stake, 'chat_id': message.chat.id}
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_ttt_open_{message.from_user.id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT))
        markup.add(btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_TTT_X} {user_display} ищет соперника!\n{EMO_TTT_INVITE} Игра: Крестики-Нолики 3х3\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'ttt', 'stake': stake, 'chat_id': message.chat.id}


def start_ttt_match(cid, p1, p2, stake):
    add_player_to_game(p1['user_id'])
    add_player_to_game(p2['user_id'])
    board = ['⬜'] * 9
    p1d = get_user_display(p1)
    p2d = get_user_display(p2)
    p1n = get_or_create_user(p1['user_id'], "", "")
    p2n = get_or_create_user(p2['user_id'], "", "")
    if p1n['balance'] > p2n['balance']:
        first = 'X'
        fd = p1d
        extra = f"({p1d} больше)"
    elif p2n['balance'] > p1n['balance']:
        first = 'O'
        fd = p2d
        extra = f"({p2d} больше)"
    else:
        first = random.choice(['X', 'O'])
        fd = p1d if first == 'X' else p2d
        extra = "(равно)"
    msg = safe_send(cid, f"{EMO_TTT_INVITE} Поле...")
    if not msg:
        return
    active_games[cid] = active_games.get(cid, {})
    active_games[cid][msg.message_id] = {
        'p1_id': p1['user_id'], 'p2_id': p2['user_id'], 'board': board, 'turn': first,
        'stake': stake, 'finished': False, 'game_type': 'ttt', 'processing': False,
        'chat_id': cid, 'msg_id': msg.message_id
    }
    fs = EMO_TTT_X if first == 'X' else EMO_TTT_O
    safe_edit(cid, msg.message_id, f"{p1d} {EMO_VS} {p2d}\n{EMO_NOX} {stake:,}\nХодит: {fd} {fs} {extra}", reply_markup=gen_ttt_board(board, msg.message_id), parse_mode='HTML')
    start_timer(cid, msg.message_id, game_type='ttt', timeout=60)


def gen_ttt_board(board, mid):
    markup = types.InlineKeyboardMarkup(row_width=3)
    symbols = {0:'1️⃣',1:'2️⃣',2:'3️⃣',3:'4️⃣',4:'5️⃣',5:'6️⃣',6:'7️⃣',7:'8️⃣',8:'9️⃣'}
    btns = []
    for i, cell in enumerate(board):
        if cell == '❌':
            btns.append(btn(' ', callback_data="ignore", icon=ICO_TTT_X))
        elif cell == '⭕':
            btns.append(btn(' ', callback_data="ignore", icon=ICO_TTT_O))
        else:
            btns.append(btn(symbols[i], callback_data=f"click_ttt_{mid}_{i}", style='primary'))
    for chunk in [btns[i:i+3] for i in range(0, 9, 3)]:
        markup.add(*chunk)
    markup.add(btn("СДАТЬСЯ", callback_data=f"surrender_ttt_{mid}", style='danger', icon=ICO_SURRENDER))
    return markup


def check_ttt_winner(b, t):
    board = []
    for cell in b:
        if cell == '❌':
            board.append('X')
        elif cell == '⭕':
            board.append('O')
        else:
            board.append(' ')
    s = 'X' if t == 'X' else 'O'
    for ln in [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]:
        if board[ln[0]] == board[ln[1]] == board[ln[2]] == s:
            return True
    return False


@bot.callback_query_handler(func=lambda call: call.data.startswith("click_ttt_"))
def click_ttt(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    parts = call.data.split("_")
    mid = int(parts[2])
    idx = int(parts[3])
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
            g['processing'] = False
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
            safe_edit(cid, mid, f"{EMO_TROPHY} {get_user_display_by_id(wid)} ПОБЕДИЛ! +{wa - g['stake']:,} ноксов {EMO_NOX}!", parse_mode='HTML')
            del active_games[cid][mid]
            remove_player_from_game(wid)
            remove_player_from_game(lid)
        elif '⬜' not in g['board']:
            update_balance(g['p1_id'], g['stake'])
            update_balance(g['p2_id'], g['stake'])
            safe_edit(cid, mid, "🤝 Ничья!")
            del active_games[cid][mid]
            remove_player_from_game(g['p1_id'])
            remove_player_from_game(g['p2_id'])
        else:
            g['turn'] = 'O' if g['turn'] == 'X' else 'X'
            nid = g['p1_id'] if g['turn'] == 'X' else g['p2_id']
            ns = EMO_TTT_X if g['turn'] == 'X' else EMO_TTT_O
            safe_edit(cid, mid, f"{EMO_TTT_INVITE} Ходит: {get_user_display_by_id(nid)} {ns}", reply_markup=gen_ttt_board(g['board'], mid), parse_mode='HTML')
            start_timer(cid, mid, game_type='ttt', timeout=60)
    except Exception as e:
        print(f"[TTT] {e}")
    g['processing'] = False


@bot.callback_query_handler(func=lambda call: call.data.startswith("surrender_ttt_"))
def surrender_ttt(call):
    safe_answer(call.id, "🏳️")
    parts = call.data.split("_")
    mid = int(parts[2])
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
    safe_edit(cid, mid, f"{EMO_SURRENDER} {get_user_display_by_id(sid)} СДАЛСЯ!\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,} ноксов {EMO_NOX}!", parse_mode='HTML')
    del active_games[cid][mid]
    remove_player_from_game(wid)
    remove_player_from_game(sid)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_ttt_open_"))
def join_ttt_open(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    parts = call.data.split("_")
    hid = int(parts[3])
    stake = int(parts[4])
    mid = int(parts[5])
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
        safe_answer(call.id, "❌ Недостаточно баланса!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    start_ttt_match(call.message.chat.id, h, gu, stake)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_ttt_"))
def join_ttt(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    parts = call.data.split("_")
    hid = int(parts[2])
    tid = int(parts[3])
    stake = int(parts[4])
    mid = int(parts[5])
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
        safe_answer(call.id, "❌ Недостаточно баланса!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    start_ttt_match(call.message.chat.id, h, gu, stake)


# ---------- МИНЫ ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith('мины'))
def cmd_mines_game(message):
    if check_pm_game(message):
        return
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id, sender_chat=message.sender_chat):
        return
    match = re.match(r'^мины\s+(\S+)$', message.text.strip().lower())
    if not match:
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    stake_arg = match.group(1).strip()
    if stake_arg == 'вб':
        stake = user['balance']
        if stake < 1:
            safe_send(message.chat.id, f"{EMO_BULB} Нет {EMO_NOX}!", parse_mode='HTML')
            return
    else:
        try:
            stake = int(stake_arg)
        except ValueError:
            safe_send(message.chat.id, f"{EMO_BULB} Число или вб!", parse_mode='HTML')
            return
        if stake < 1:
            safe_send(message.chat.id, f"{EMO_BULB} Ставка > 0!", parse_mode='HTML')
            return
    if user['balance'] < stake:
        safe_send(message.chat.id, f"{EMO_BULB} Недостаточно баланса! Нужно <b>{stake:,}</b>, у тебя <b>{user['balance']:,}</b> ноксов {EMO_NOX}", parse_mode='HTML')
        return
    if check_player_in_game(message.from_user.id):
        force_cleanup_player(message.from_user.id)
    user_display = get_user_display(user)
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target = get_or_create_user(target_id, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
        target_display = get_user_display(target)
        if target_id == user['user_id']:
            safe_send(message.chat.id, f"{EMO_BULB} С собой нельзя!", parse_mode='HTML')
            return
        if target['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} У соперника мало баланса! Нужно <b>{stake:,}</b>, у него <b>{target['balance']:,}</b> {EMO_NOX}", parse_mode='HTML')
            return
        if check_player_in_game(target_id):
            safe_send(message.chat.id, f"{EMO_BULB} Соперник уже в игре!", parse_mode='HTML')
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_mines_{message.from_user.id}_{target_id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT))
        markup.add(btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_MINE} {user_display} вызывает {target_display}!\n{EMO_SOLO_HEADER} Игра: Минное поле 5x5\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'mines', 'stake': stake, 'chat_id': message.chat.id}
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_mines_open_{message.from_user.id}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT))
        markup.add(btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_MINE} {user_display} ищет соперника!\n{EMO_SOLO_HEADER} Игра: Минное поле 5x5\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
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
    p1d = get_user_display(p1)
    p2d = get_user_display(p2)
    if p1n['balance'] > p2n['balance']:
        fp = 1
        fd = p1d
        extra = f"({p1d} больше)"
    elif p2n['balance'] > p1n['balance']:
        fp = 2
        fd = p2d
        extra = f"({p2d} больше)"
    else:
        fp = random.choice([1, 2])
        fd = p1d if fp == 1 else p2d
        extra = "(равно)"
    msg = safe_send(cid, f"{EMO_MINE} Минное поле 5x5", parse_mode='HTML')
    if not msg:
        return
    active_games[cid] = active_games.get(cid, {})
    active_games[cid][msg.message_id] = {
        'p1_id': p1['user_id'], 'p2_id': p2['user_id'], 'board': board, 'mines': mines,
        'turn': fp, 'stake': stake, 'game_type': 'mines', 'finished': False, 'processing': False,
        'chat_id': cid, 'msg_id': msg.message_id
    }
    safe_edit(cid, msg.message_id, f"{EMO_MINE}\n{p1d} {EMO_VS} {p2d}\n{EMO_NOX} {stake:,} | {fd} {extra}", reply_markup=gen_mines_board(board, msg.message_id), parse_mode='HTML')
    start_timer(cid, msg.message_id, game_type='mines', timeout=60)


def gen_mines_board(board, mid):
    markup = types.InlineKeyboardMarkup(row_width=5)
    btns = []
    for i, cell in enumerate(board):
        if cell in ('⬜', '❓'):
            btns.append(btn('❓', callback_data=f"click_mines_{mid}_{i}", style='primary'))
        elif cell == '✅':
            btns.append(btn(' ', callback_data="ignore", icon=ICO_SAFE))
        else:
            btns.append(btn(' ', callback_data="ignore", icon=ICO_MINE))
    for chunk in [btns[i:i+5] for i in range(0, 25, 5)]:
        markup.add(*chunk)
    markup.add(btn("СДАТЬСЯ", callback_data=f"surrender_mines_{mid}", style='danger', icon=ICO_SURRENDER))
    return markup


def gen_mines_final(mines):
    markup = types.InlineKeyboardMarkup(row_width=5)
    btns = [btn(' ', callback_data="ignore", icon=ICO_MINE if m else ICO_SAFE) for m in mines]
    for chunk in [btns[i:i+5] for i in range(0, 25, 5)]:
        markup.add(*chunk)
    return markup


@bot.callback_query_handler(func=lambda call: call.data.startswith("click_mines_"))
def click_mines(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    parts = call.data.split("_")
    mid = int(parts[2])
    idx = int(parts[3])
    cid = call.message.chat.id
    uid = call.from_user.id
    if mid not in active_games.get(cid, {}):
        safe_answer(call.id, "❌", show_alert=True)
        return
    g = active_games[cid][mid]
    if g.get('finished', False) or g.get('processing', False):
        return
    g['processing'] = True
    try:
        ct = g['p1_id'] if g['turn'] == 1 else g['p2_id']
        if uid != ct:
            g['processing'] = False
            safe_answer(call.id, "❌ Не твой ход!", show_alert=True)
            return
        if g['board'][idx] not in ('⬜', '❓'):
            g['processing'] = False
            return
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
            safe_edit(cid, mid, f"{EMO_MINE} {get_user_display_by_id(lid)} на мине!\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,} ноксов {EMO_NOX}!", reply_markup=gen_mines_final(g['mines']), parse_mode='HTML')
            del active_games[cid][mid]
            remove_player_from_game(wid)
            remove_player_from_game(lid)
        else:
            g['board'][idx] = '✅'
            sc = [i for i, m in enumerate(g['mines']) if not m]
            op = [i for i, c in enumerate(g['board']) if c == '✅']
            if len(op) == len(sc):
                update_balance(g['p1_id'], g['stake'])
                update_balance(g['p2_id'], g['stake'])
                g['finished'] = True
                safe_edit(cid, mid, "🤝 Ничья!", reply_markup=gen_mines_final(g['mines']), parse_mode='HTML')
                del active_games[cid][mid]
                remove_player_from_game(g['p1_id'])
                remove_player_from_game(g['p2_id'])
            else:
                g['turn'] = 2 if g['turn'] == 1 else 1
                nid = g['p1_id'] if g['turn'] == 1 else g['p2_id']
                safe_edit(cid, mid, f"{EMO_MINE}\n{EMO_NOX} {g['stake']:,} | {get_user_display_by_id(nid)}", reply_markup=gen_mines_board(g['board'], mid), parse_mode='HTML')
                start_timer(cid, mid, game_type='mines', timeout=60)
    except Exception as e:
        print(f"[MINES] {e}")
    g['processing'] = False


@bot.callback_query_handler(func=lambda call: call.data.startswith("surrender_mines_"))
def surrender_mines(call):
    safe_answer(call.id, "🏳️")
    parts = call.data.split("_")
    mid = int(parts[2])
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
    safe_edit(cid, mid, f"{EMO_SURRENDER} {get_user_display_by_id(sid)} СДАЛСЯ!\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,} ноксов {EMO_NOX}!", reply_markup=gen_mines_final(g['mines']), parse_mode='HTML')
    del active_games[cid][mid]
    remove_player_from_game(wid)
    remove_player_from_game(sid)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_mines_open_"))
def join_mines_open(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    parts = call.data.split("_")
    hid = int(parts[3])
    stake = int(parts[4])
    mid = int(parts[5])
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
        safe_answer(call.id, "❌ Недостаточно баланса!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    start_mines_match(call.message.chat.id, h, gu, stake)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_mines_"))
def join_mines(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    parts = call.data.split("_")
    hid = int(parts[2])
    tid = int(parts[3])
    stake = int(parts[4])
    mid = int(parts[5])
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
        safe_answer(call.id, "❌ Недостаточно баланса!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    start_mines_match(call.message.chat.id, h, gu, stake)


# ---------- УГАДАЙ ЧИСЛО ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower().startswith('число') and m.chat.type in ['group', 'supergroup'])
def cmd_number_game(message):
    if check_banned(message.from_user.id, message.chat.id):
        return
    if not check_required_subscriptions(message.from_user.id, message.chat.id, message.message_id, sender_chat=message.sender_chat):
        return
    match = re.match(r'^число\s+(\d+)\s+(\S+)$', message.text.strip().lower())
    if not match:
        safe_send(message.chat.id, f"{EMO_BULB} Формат: <code>число 100 [ставка]</code>", parse_mode='HTML')
        return
    mx = int(match.group(1))
    sa = match.group(2).strip()
    if mx < 2:
        safe_send(message.chat.id, f"{EMO_BULB} Диапазон > 1!", parse_mode='HTML')
        return
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    if sa == 'вб':
        stake = user['balance']
        if stake < 1:
            safe_send(message.chat.id, f"{EMO_BULB} Нет {EMO_NOX}!", parse_mode='HTML')
            return
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
        safe_send(message.chat.id, f"{EMO_BULB} Недостаточно баланса! Нужно <b>{stake:,}</b>, у тебя <b>{user['balance']:,}</b> ноксов {EMO_NOX}", parse_mode='HTML')
        return
    if check_player_in_game(message.from_user.id):
        force_cleanup_player(message.from_user.id)
    user_display = get_user_display(user)
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target = get_or_create_user(target_id, message.reply_to_message.from_user.username, message.reply_to_message.from_user.first_name)
        target_display = get_user_display(target)
        if target_id == user['user_id']:
            safe_send(message.chat.id, f"{EMO_BULB} С собой нельзя!", parse_mode='HTML')
            return
        if target['balance'] < stake:
            safe_send(message.chat.id, f"{EMO_BULB} У соперника мало баланса! Нужно <b>{stake:,}</b>, у него <b>{target['balance']:,}</b> {EMO_NOX}", parse_mode='HTML')
            return
        if check_player_in_game(target_id):
            safe_send(message.chat.id, f"{EMO_BULB} Соперник уже в игре!", parse_mode='HTML')
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_number_{message.from_user.id}_{target_id}_{mx}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT))
        markup.add(btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_NUMBER} {user_display} вызывает {target_display}!\n{EMO_SOLO_HEADER} Игра: Угадай число (1-{mx})\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'number', 'stake': stake, 'chat_id': message.chat.id, 'max_num': mx}
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(btn("Принять", callback_data=f"join_number_open_{message.from_user.id}_{mx}_{stake}_{message.message_id}", style='success', icon=ICO_ACCEPT))
        markup.add(btn("Отмена", callback_data=f"cancel_invite_{message.message_id}", style='danger', icon=ICO_CANCEL))
        safe_send(message.chat.id, f"{EMO_NUMBER} {user_display} ищет соперника!\n{EMO_SOLO_HEADER} Игра: Угадай число (1-{mx})\n{EMO_NOX} Ставка: <b>{stake:,}</b>", parse_mode='HTML', reply_markup=markup)
        invites[message.message_id] = {'host_id': message.from_user.id, 'game_type': 'number', 'stake': stake, 'chat_id': message.chat.id, 'max_num': mx}


def start_number_match(cid, p1, p2, mx, stake):
    add_player_to_game(p1['user_id'])
    add_player_to_game(p2['user_id'])
    secret = random.randint(1, mx)
    p1d = get_user_display(p1)
    p2d = get_user_display(p2)
    if p1['balance'] > p2['balance']:
        turn = p1['user_id']
        td = p1d
    elif p2['balance'] > p1['balance']:
        turn = p2['user_id']
        td = p2d
    else:
        turn = random.choice([p1['user_id'], p2['user_id']])
        td = p1d if turn == p1['user_id'] else p2d
    msg = safe_send(cid, f"{EMO_NUMBER} Игра!\n{p1d} {EMO_VS} {p2d}\n1-{mx}\n{EMO_NOX} {stake:,}\nХодит: {td}", parse_mode='HTML')
    if not msg:
        return
    active_games[cid] = active_games.get(cid, {})
    active_games[cid][msg.message_id] = {
        'p1_id': p1['user_id'], 'p2_id': p2['user_id'], 'secret': secret, 'max_num': mx,
        'stake': stake, 'turn': turn, 'finished': False, 'game_type': 'number',
        'chat_id': cid, 'msg_id': msg.message_id, 'attempts': [], 'timer_id': None
    }
    start_number_timer(cid, msg.message_id)


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
        safe_send(cid, f"{EMO_TIMER} {get_user_display_by_id(cur)} не сходил!\n{EMO_CROWN} {get_user_display_by_id(opp)} +{wa - gg['stake']:,} ноксов {EMO_NOX}!\n📝 {at}", parse_mode='HTML')
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
    parts = call.data.split("_")
    hid = int(parts[3])
    mx = int(parts[4])
    stake = int(parts[5])
    mid = int(parts[6])
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
        safe_answer(call.id, "❌ Недостаточно баланса!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    start_number_match(call.message.chat.id, h, gu, mx, stake)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_number_"))
def join_number(call):
    if check_banned(call.from_user.id, call.message.chat.id):
        return
    parts = call.data.split("_")
    hid = int(parts[2])
    tid = int(parts[3])
    mx = int(parts[4])
    stake = int(parts[5])
    mid = int(parts[6])
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
        safe_answer(call.id, "❌ Недостаточно баланса!", show_alert=True)
        return
    update_balance(hid, -stake)
    update_balance(uid, -stake)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
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
    except:
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
                        c_i = g.get('chooser_id')
                        gs_i = g.get('guesser_id')
                        st = g.get('stake')
                        if c_i and gs_i:
                            update_balance(c_i, st)
                            update_balance(gs_i, st)
                            remove_player_from_game(c_i)
                            remove_player_from_game(gs_i)
                        safe_edit(cid, mid, f"{EMO_TIMER} Время вышло. Ставки возвращены.", parse_mode='HTML')
                        del active_games[cid][gid]
                        break
            if mid in invites:
                del invites[mid]
            return
        if game_type == 'eagle_guess':
            if cid in active_games:
                for gid, g in list(active_games[cid].items()):
                    if g.get('msg_id') == mid and g.get('game_type') == 'eagle_guess' and not g.get('finished', False):
                        g['finished'] = True
                        c_i = g['chooser_id']
                        gs_i = g['guesser_id']
                        st = g['stake']
                        wa = st * 2
                        update_balance(c_i, wa)
                        update_streak(c_i, True, st)
                        update_streak(gs_i, False, st)
                        update_game_stats(c_i, 'eagle', True)
                        update_game_stats(gs_i, 'eagle', False)
                        safe_edit(cid, mid, f"{EMO_TIMER} {get_user_display_by_id(gs_i)} не угадал!\n{EMO_CROWN} {get_user_display_by_id(c_i)} +{wa - st:,} ноксов {EMO_NOX}!", parse_mode='HTML')
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
                safe_edit(cid, mid, f"{EMO_TIMER} {get_user_display_by_id(lid)} не сделал!\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,}!", parse_mode='HTML')
                del active_games[cid][mid]
                remove_player_from_game(wid)
                remove_player_from_game(lid)
        elif game_type == 'ttt':
            if g['turn'] == 'X':
                cur, opp = g['p1_id'], g['p2_id']
            else:
                cur, opp = g['p2_id'], g['p1_id']
            g['finished'] = True
            wa = g['stake'] * 2
            update_balance(opp, wa)
            update_streak(opp, True, g['stake'])
            update_streak(cur, False, g['stake'])
            update_game_stats(opp, 'ttt', True)
            update_game_stats(cur, 'ttt', False)
            safe_edit(cid, mid, f"{EMO_TIMER} {get_user_display_by_id(cur)} не сходил!\n{EMO_CROWN} {get_user_display_by_id(opp)} +{wa - g['stake']:,}!", parse_mode='HTML')
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
            safe_edit(cid, mid, f"{EMO_TIMER} {get_user_display_by_id(cur)} не сходил!\n{EMO_CROWN} {get_user_display_by_id(opp)} +{wa - g['stake']:,}!", reply_markup=gen_mines_final(g['mines']), parse_mode='HTML')
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
            safe_edit(cid, mid, f"{EMO_TIMER} {get_user_display_by_id(cur)} не выстрелил!\n{EMO_CROWN} {get_user_display_by_id(opp)} +{wa - g['stake']:,}!", parse_mode='HTML')
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


# ---------- АДМИН-ПАНЕЛЬ ----------

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel" and call.from_user.id == OWNER_ID)
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
    markup.add(btn("Символы кланов", callback_data="adm_clan_emojis", style='success', icon=ICO_PROMO))
    markup.add(btn("Короны лидера", callback_data="adm_clan_crowns", style='success', icon=ICO_ADMIN))
    markup.add(btn("Список кланов", callback_data="adm_clans_list", style='primary', icon=ICO_ADMIN))
    markup.add(btn("Перезагрузить бота", callback_data="adm_restart", style='danger', icon=ICO_TIMER))
    markup.add(btn("Назад", callback_data="back_to_menu", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, f"{EMO_ADMIN} <b>Админ-панель</b>", reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "adm_restart" and call.from_user.id == OWNER_ID)
def adm_restart(call):
    safe_answer(call.id, "🔄")
    safe_edit(call.message.chat.id, call.message.message_id, f"{EMO_TIMER} Перезагрузка...", parse_mode='HTML')
    time.sleep(1)
    try:
        subprocess.Popen([sys.executable] + sys.argv, stdout=open('bot.log', 'a'), stderr=subprocess.STDOUT, start_new_session=True)
    except:
        pass
    os._exit(0)


@bot.callback_query_handler(func=lambda call: call.data == "adm_refill_input" and call.from_user.id == OWNER_ID)
def adm_refill_input(call):
    msg = safe_send(call.message.chat.id, f"{EMO_NOX} Сумма:", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_admin_refill)
    safe_answer(call.id)


def process_admin_refill(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        a = int(message.text.strip())
        if a <= 0:
            return
        update_balance(OWNER_ID, a)
        u = get_or_create_user(OWNER_ID, "", "")
        safe_send(message.chat.id, f"{EMO_SAFE} +{a:,}! Баланс: <code>{u['balance']:,}</code>", parse_mode='HTML')
    except:
        safe_send(message.chat.id, f"{EMO_CANCEL} Число!", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "adm_reset_balance" and call.from_user.id == OWNER_ID)
def adm_reset_balance(call):
    set_balance(OWNER_ID, 0)
    safe_send(call.message.chat.id, f"{EMO_CANCEL} Обнулён!", parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "adm_mailing" and call.from_user.id == OWNER_ID)
def adm_mailing(call):
    msg = safe_send(call.message.chat.id, f"{EMO_CHANNEL} Текст:", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_mailing)
    safe_answer(call.id)


def process_mailing(message):
    if message.from_user.id != OWNER_ID:
        return
    t = message.text
    if not t:
        return
    us = get_all_users()
    s = 0
    f = 0
    for r in us:
        if r['user_id'] == OWNER_ID:
            continue
        try:
            bot.send_message(r['user_id'], t, parse_mode='HTML')
            s += 1
            time.sleep(0.05)
        except:
            f += 1
    ch = get_all_chats()
    sc = 0
    cf = 0
    for r in ch:
        try:
            bot.send_message(r['chat_id'], t, parse_mode='HTML')
            sc += 1
            time.sleep(0.05)
        except:
            cf += 1
    safe_send(message.chat.id, f"📢 Рассылка завершена\n✅ ЛС: {s} | ❌ ЛС: {f}\n✅ Чаты: {sc} | ❌ Чаты: {cf}", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "adm_user_add" and call.from_user.id == OWNER_ID)
def adm_user_add(call):
    msg = safe_send(call.message.chat.id, f"{EMO_NOX} ID сумма:", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_admin_add_user)
    safe_answer(call.id)


def process_admin_add_user(message):
    if message.from_user.id != OWNER_ID:
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
    except:
        safe_send(message.chat.id, f"{EMO_CANCEL} Формат: ID сумма", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "adm_gen_promo" and call.from_user.id == OWNER_ID)
def adm_gen_promo(call):
    msg = safe_send(call.message.chat.id, "Введи: <b>код</b> <b>активаций</b> <b>сумма</b>\nПример: <code>норик топ 10 1000</code> — код <b>норик топ</b>, 10 активаций, 1000 ноксов", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_promo_create)
    safe_answer(call.id)


def process_promo_create(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        parts = message.text.strip().split()
        if len(parts) < 3:
            raise ValueError("Мало параметров")
        mx = int(parts[-2])
        rw = int(parts[-1])
        code = " ".join(parts[:-2])
        if not code or mx <= 0 or rw <= 0:
            raise ValueError("Пустой код / ноль")
        with db_lock:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO promos (code, reward, max_uses, current_uses)
                VALUES (%s, %s, %s, 0)
                ON CONFLICT (code) DO UPDATE SET reward = EXCLUDED.reward, max_uses = EXCLUDED.max_uses, current_uses = 0
            ''', (code, rw, mx))
            conn.commit()
            cur.close()
            conn.close()
        safe_send(message.chat.id, f"{EMO_SAFE} Промокод: <code>{code}</code>\n💰 Награда: <b>{rw:,}</b>\n👥 Активаций: <b>{mx}</b>", parse_mode='HTML')
    except Exception:
        safe_send(message.chat.id, "❌ Формат: <b>код</b> <b>активаций</b> <b>сумма</b>\nПример: <code>норик топ 10 1000</code>", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "adm_users_list" and call.from_user.id == OWNER_ID)
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
    if page < 0:
        page = 0
    if page >= pages:
        page = pages - 1
    st = page * pp
    en = min(st + pp, total)
    t = f"👥 <b>Юзеры</b> ({total}, стр. {page+1}/{pages})\n"
    for i in range(st, en):
        row = rows[i]
        t += f"{i+1}. {get_user_display(row)} — <code>{row['balance']:,}</code> ноксов\n"
    markup = types.InlineKeyboardMarkup(row_width=2)
    if page > 0:
        markup.add(btn("◀️ Назад", callback_data=f"user_page_{page-1}", style='primary', icon=ICO_BACK))
    if page < pages - 1:
        markup.add(btn("Вперёд ▶️", callback_data=f"user_page_{page+1}", style='primary'))
    if pages > 1:
        markup.add(btn(f"📊 {page+1}/{pages}", callback_data="ignore"))
    markup.add(btn("В админку", callback_data="admin_panel", style='danger', icon=ICO_BACK))
    if mid:
        safe_edit(cid, mid, t, parse_mode='HTML', reply_markup=markup)
    else:
        safe_send(cid, t, parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("user_page_") and call.from_user.id == OWNER_ID)
def user_page_callback(call):
    page = int(call.data.split("_")[2])
    show_user_page(call.message.chat.id, call.from_user.id, page, call.message.message_id)
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: (call.data == "adm_promo_history" or call.data.startswith("adm_promo_page_")) and call.from_user.id == OWNER_ID)
def adm_promo_history(call):
    safe_answer(call.id)
    page = 1
    if call.data.startswith("adm_promo_page_"):
        page = int(call.data.split("_")[3])
    try:
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT code, reward, max_uses, current_uses FROM promos ORDER BY code DESC')
            all_promos = cursor.fetchall()
            if not all_promos:
                safe_send(call.message.chat.id, f"{EMO_CANCEL} Промокодов нет.", parse_mode='HTML')
                cursor.close()
                conn.close()
                return
            total_pages = (len(all_promos) + PROMOS_PER_PAGE - 1) // PROMOS_PER_PAGE
            page = max(1, min(page, total_pages))
            start_idx = (page - 1) * PROMOS_PER_PAGE
            page_promos = all_promos[start_idx:start_idx + PROMOS_PER_PAGE]
            text = f"📋 <b>ИСТОРИЯ АКТИВАЦИЙ (Стр. {page}/{total_pages})</b>\n"
            for promo in page_promos:
                code = promo['code']
                text += f"\n<b>Код:</b> <code>{code}</code>\n"
                text += f"{EMO_NOX} Награда: <b>{promo['reward']:,}</b> ноксов\n"
                text += f"👥 Активаций: <b>{promo['current_uses']}/{promo['max_uses']}</b>\n"
                cursor.execute('SELECT u.username, u.first_name, ph.activated_at FROM promo_history ph JOIN users u ON ph.user_id = u.user_id WHERE ph.code = %s ORDER BY ph.activated_at DESC', (code,))
                users = cursor.fetchall()
                if users:
                    user_list = []
                    for u in users:
                        name = f"@{u['username']}" if u['username'] else u['first_name']
                        date = str(u['activated_at'])[:16] if u['activated_at'] else ''
                        user_list.append(f"{name} ({date})")
                    text += "👤 Активировали:\n" + "\n".join(f"   • {u}" for u in user_list) + "\n"
                else:
                    text += "👤 Активировали: <i>никто</i>\n"
            cursor.close()
            conn.close()
        markup = types.InlineKeyboardMarkup()
        nav_buttons = []
        if page > 1:
            nav_buttons.append(btn("◀️ Назад", callback_data=f"adm_promo_page_{page - 1}", style='primary', icon=ICO_BACK))
        if page < total_pages:
            nav_buttons.append(btn("Вперед ▶️", callback_data=f"adm_promo_page_{page + 1}", style='primary'))
        if nav_buttons:
            markup.row(*nav_buttons)
        markup.add(btn("В админку", callback_data="admin_panel", style='danger', icon=ICO_BACK))
        if call.data.startswith("adm_promo_page_"):
            safe_edit(call.message.chat.id, call.message.message_id, text, parse_mode='HTML', reply_markup=markup)
        else:
            safe_send(call.message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        safe_send(call.message.chat.id, f"Ошибка: <code>{e}</code>", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "adm_subscriptions" and call.from_user.id == OWNER_ID)
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


@bot.callback_query_handler(func=lambda call: call.data == "add_sub_start" and call.from_user.id == OWNER_ID)
def add_sub_start(call):
    msg = safe_send(call.message.chat.id, f"{EMO_INPUT} Введи: <b>ID_канала</b> <b>тип</b> <b>ссылка</b> <b>название</b>\nПример: <code>-1001234567890 channel @mychannel Мой канал</code>", parse_mode='HTML')
    if msg:
        bot.register_next_step_handler(msg, process_add_sub)
    safe_answer(call.id)


def process_add_sub(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        parts = message.text.strip().split(maxsplit=3)
        chat_id = int(parts[0])
        type_ = parts[1]
        link = parts[2]
        title = parts[3]
        add_required_subscription(chat_id, type_, link, title)
        safe_send(message.chat.id, f"{EMO_SAFE} {title} добавлена!", parse_mode='HTML')
    except Exception as e:
        safe_send(message.chat.id, f"{EMO_CANCEL} Ошибка: {e}", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data.startswith("del_sub_") and call.from_user.id == OWNER_ID)
def del_sub(call):
    sid = int(call.data.split("_")[2])
    try:
        remove_required_subscription(sid)
        safe_answer(call.id, "✅")
    except Exception as e:
        safe_answer(call.id, f"❌ {e}", show_alert=True)
    adm_subscriptions(call)


@bot.callback_query_handler(func=lambda call: call.data == "adm_subscription_management" and call.from_user.id == OWNER_ID)
def adm_subscription_management(call):
    bot_id = get_bot_id()
    chats = get_all_chats()
    admin_chats = []
    for row in chats:
        try:
            m = bot.get_chat_member(row['chat_id'], bot_id)
            if m.status in ('administrator', 'creator'):
                admin_chats.append(row)
            else:
                with db_lock:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM chats WHERE chat_id = %s', (row['chat_id'],))
                    conn.commit()
                    cursor.close()
                    conn.close()
        except:
            with db_lock:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('DELETE FROM chats WHERE chat_id = %s', (row['chat_id'],))
                conn.commit()
                cursor.close()
                conn.close()
    text = f"{EMO_CHAT} <b>Чаты где бот админ</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    if admin_chats:
        for row in admin_chats:
            st = "✅" if row['sub_required'] else "❌"
            ns = 0 if row['sub_required'] else 1
            title = row['chat_title'] or row['chat_id']
            markup.add(btn(f"{st} {title}", callback_data=f"toggle_subreq_{row['chat_id']}_{ns}", style='primary', icon=ICO_CHAT))
            markup.add(btn(f"🗑 Удалить", callback_data=f"del_chat_{row['chat_id']}", style='danger', icon=ICO_CANCEL))
    else:
        text += "Нет.\n"
    markup.add(btn("Назад", callback_data="admin_panel", style='danger', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, reply_markup=markup, parse_mode='HTML')
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("del_chat_") and call.from_user.id == OWNER_ID)
def del_chat(call):
    cid = int(call.data.split("_")[2])
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM chats WHERE chat_id = %s', (cid,))
        conn.commit()
        cursor.close()
        conn.close()
    safe_answer(call.id, "✅ Удалено!")
    adm_subscription_management(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_subreq_") and call.from_user.id == OWNER_ID)
def toggle_subreq(call):
    p = call.data.split("_")
    cid = int(p[2])
    ns = int(p[3])
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE chats SET sub_required = %s WHERE chat_id = %s', (ns, cid))
        conn.commit()
        cursor.close()
        conn.close()
    safe_answer(call.id, "✅")
    adm_subscription_management(call)


# ---------- АДМИНКА: СИМВОЛЫ И КОРОНЫ ----------

LAST_OWNER_SECTION = {'value': 'symbols'}


@bot.callback_query_handler(func=lambda call: call.data == "adm_clan_emojis" and call.from_user.id == OWNER_ID)
def adm_clan_emojis(call):
    LAST_OWNER_SECTION['value'] = 'symbols'
    show_clan_emojis_admin(call.message.chat.id, call.message.message_id)
    safe_answer(call.id)


def show_clan_emojis_admin(chat_id, mid):
    emojis = get_clan_emojis()
    text = f"🎨 <b>СИМВОЛЫ КЛАНОВ</b>\n\nЗагружено: <b>{len(emojis)}</b> символов\n\n"
    text += "Кидай премиум-эмодзи в чат — бот сохранит автоматически.\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(btn("🗑 Очистить все", callback_data="adm_clan_emojis_clear", style='danger', icon=ICO_CANCEL))
    markup.add(btn("Назад", callback_data="admin_panel", style='primary', icon=ICO_BACK))
    safe_edit(chat_id, mid, text, parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "adm_clan_emojis_clear" and call.from_user.id == OWNER_ID)
def adm_clan_emojis_clear(call):
    clear_clan_emojis()
    safe_answer(call.id, "✅ Очищено", show_alert=True)
    show_clan_emojis_admin(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "adm_clan_crowns" and call.from_user.id == OWNER_ID)
def adm_clan_crowns(call):
    LAST_OWNER_SECTION['value'] = 'crowns'
    show_clan_crowns_admin(call.message.chat.id, call.message.message_id)
    safe_answer(call.id)


def show_clan_crowns_admin(chat_id, mid):
    crowns = get_clan_crowns()
    text = f"👑 <b>КОРОНЫ ЛИДЕРА</b>\n\nЗагружено: <b>{len(crowns)}</b> корон\n\n"
    text += "Кидай премиум-эмодзи в чат — бот сохранит автоматически.\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(btn("🗑 Очистить все", callback_data="adm_clan_crowns_clear", style='danger', icon=ICO_CANCEL))
    markup.add(btn("Назад", callback_data="admin_panel", style='primary', icon=ICO_BACK))
    safe_edit(chat_id, mid, text, parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "adm_clan_crowns_clear" and call.from_user.id == OWNER_ID)
def adm_clan_crowns_clear(call):
    clear_clan_crowns()
    safe_answer(call.id, "✅ Очищено", show_alert=True)
    show_clan_crowns_admin(call.message.chat.id, call.message.message_id)


@bot.message_handler(content_types=['text'], func=lambda m: m.from_user.id == OWNER_ID and m.chat.type == 'private')
def owner_catch_emoji(message):
    if not message.entities:
        return
    target = LAST_OWNER_SECTION['value']
    added_sym = 0
    added_crn = 0
    for ent in message.entities:
        try:
            if ent.type == 'custom_emoji':
                eid = ent.custom_emoji_id
                fallback = message.text[ent.offset:ent.offset + ent.length] if message.text else '🏰'
                if target == 'crowns':
                    if add_clan_crown(eid, fallback):
                        added_crn += 1
                else:
                    if add_clan_emoji(eid, fallback):
                        added_sym += 1
        except Exception:
            continue
    parts = []
    if added_sym:
        parts.append(f"символов: {added_sym}")
    if added_crn:
        parts.append(f"корон: {added_crn}")
    if parts:
        safe_send(message.chat.id, f"✅ Сохранено {', '.join(parts)}", parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "adm_clans_list" and call.from_user.id == OWNER_ID)
def adm_clans_list(call):
    clans = get_all_clans()
    text = f"{EMO_CLAN_HEADER} <b>СПИСОК КЛАНОВ</b>\n\nВсего: <b>{len(clans)}</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for c in clans:
        m = get_clan_member_count(c['id'])
        crown = render_leader_crown(c)
        text += f"• {crown} {render_clan_name(c)} — {m}/{c['max_members']} | лидер: {get_user_display_by_id(c['leader_id'])}\n"
        markup.add(btn(f"🗑 Удалить {c['name']}", callback_data=f"adm_clan_del_{c['id']}", style='danger', icon=ICO_CANCEL))
    markup.add(btn("Назад", callback_data="admin_panel", style='primary', icon=ICO_BACK))
    safe_edit(call.message.chat.id, call.message.message_id, text, parse_mode='HTML', reply_markup=markup)
    safe_answer(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_clan_del_") and call.from_user.id == OWNER_ID)
def adm_clan_del(call):
    clan_id = int(call.data.split("_")[3])
    clan = get_clan_by_id(clan_id)
    if clan:
        members = get_clan_members(clan_id)
        for m in members:
            try:
                bot.send_message(m['user_id'], f"⚠️ Клан {render_clan_name(clan)} был удалён администратором.", parse_mode='HTML')
            except Exception:
                pass
        delete_clan(clan_id)
    safe_answer(call.id, "✅ Удалён", show_alert=True)
    adm_clans_list(call)


@bot.callback_query_handler(func=lambda call: call.data == "ignore")
def ignore_callback(call):
    safe_answer(call.id)


# ---------- ОБРАБОТКА СООБЩЕНИЙ "УГАДАЙ ЧИСЛО" ----------

def _has_active_number_game(chat_id):
    if chat_id not in active_games:
        return False
    for g in active_games[chat_id].values():
        if g.get('game_type') == 'number' and not g.get('finished', False):
            return True
    return False


@bot.message_handler(content_types=['text'],
                     func=lambda m: m.chat.type in ['group', 'supergroup'] and _has_active_number_game(m.chat.id))
def handle_number_game_messages(message):
    if not message.text:
        return
    text = message.text.strip()
    lowered = text.lower()
    if lowered != 'сдаюсь' and not lowered.isdigit():
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
    if lowered == 'сдаюсь':
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
        safe_send(cid, f"{EMO_SURRENDER} {get_user_display_by_id(sid)} СДАЛСЯ!\n{EMO_CROWN} {get_user_display_by_id(wid)} +{wa - g['stake']:,} ноксов {EMO_NOX}!", parse_mode='HTML')
        del active_games[cid][gmid]
        if not active_games[cid]:
            del active_games[cid]
        remove_player_from_game(wid)
        remove_player_from_game(sid)
        return
    try:
        guess = int(text)
    except:
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
        safe_send(cid, f"🎉 {get_user_display_by_id(wid)} угадал {g['secret']}!\n📝 {at}\n{EMO_CROWN} +{wa - g['stake']:,} ноксов {EMO_NOX}!", parse_mode='HTML')
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


# ---------- ФИНАЛЬНЫЕ ХЭНДЛЕРЫ КЛАНОВ ----------

@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == 'кланы')
def cmd_clans_final(message):
    try:
        text, markup = build_clans_list_text(0)
        safe_send(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"[CLANS-FINAL ERR] {e}")
        safe_send(message.chat.id, f"{EMO_CANCEL} Ошибка: {e}", parse_mode='HTML')


@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() in ('клан', 'мой клан'))
def cmd_my_clan_final(message):
    try:
        text, markup = build_my_clan_text(message.from_user.id)
        safe_send(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"[MYCLAN-FINAL ERR] {e}")
        safe_send(message.chat.id, f"{EMO_CANCEL} Ошибка: {e}", parse_mode='HTML')


if __name__ == '__main__':
    init_db()
    print("🤖 NoxHub запущен! (PostgreSQL)")
    bot.infinity_polling(allowed_updates=['message', 'callback_query', 'chat_member', 'my_chat_member', 'left_chat_member'])
