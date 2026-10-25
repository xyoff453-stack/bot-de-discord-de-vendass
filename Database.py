"""SQLite com migrações versionadas. Nunca apaga dados existentes."""
import sqlite3, threading, logging, time
from pathlib import Path

log = logging.getLogger("db")
BASE = Path(__file__).parent
DB_PATH = BASE / "data" / "bot.db"
DB_PATH.parent.mkdir(exist_ok=True)

_lock = threading.Lock()
db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
db.row_factory = sqlite3.Row
db.execute("PRAGMA journal_mode=WAL")
db.execute("PRAGMA foreign_keys=ON")

SCHEMA_VERSION = 3

def _ensure_version_table():
    db.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY CHECK (id=1),
            version INTEGER NOT NULL
        )
    """)
    row = db.execute("SELECT version FROM schema_version WHERE id=1").fetchone()
    if row is None:
        db.execute("INSERT INTO schema_version (id, version) VALUES (1, 0)")
        db.commit()
        return 0
    return row[0]

def _set_version(v):
    db.execute("UPDATE schema_version SET version=? WHERE id=1", (v,))
    db.commit()

def _migrate_v0_to_v1():
    """Schema original do bot de vendas (preservado)."""
    db.executescript("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT, server_id INTEGER NOT NULL,
        nome TEXT NOT NULL, emoji TEXT DEFAULT '📦', ordem INTEGER DEFAULT 0,
        UNIQUE(server_id, nome));
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, server_id INTEGER NOT NULL,
        nome TEXT NOT NULL, descricao TEXT, valor REAL NOT NULL,
        quantidade INTEGER DEFAULT 0, criado_em INTEGER NOT NULL,
        categoria TEXT DEFAULT 'Geral');
    CREATE TABLE IF NOT EXISTS estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER NOT NULL,
        server_id INTEGER NOT NULL, conteudo TEXT NOT NULL, data_adicao INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS msg_produto (
        produto_id INTEGER PRIMARY KEY, server_id INTEGER NOT NULL,
        canal_id INTEGER NOT NULL, msg_id INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS carrinhos (
        user_id INTEGER NOT NULL, server_id INTEGER NOT NULL,
        msg_carrinho_status INTEGER, PRIMARY KEY (user_id, server_id));
    CREATE TABLE IF NOT EXISTS carrinho_itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        server_id INTEGER NOT NULL, msg_produto_id INTEGER NOT NULL,
        produto_id INTEGER NOT NULL, produto_nome TEXT NOT NULL,
        produto_conteudo TEXT NOT NULL, produto_valor REAL NOT NULL,
        produto_data_adicao INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY, server_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        valor REAL NOT NULL, confirmado INTEGER DEFAULT 0, data TEXT, qr_code TEXT);
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, server_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL, produto_id INTEGER NOT NULL,
        produto_nome TEXT NOT NULL, valor REAL NOT NULL, data INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS idx_estq ON estoque(produto_id, server_id);
    CREATE INDEX IF NOT EXISTS idx_cart ON carrinho_itens(user_id, server_id);
    CREATE INDEX IF NOT EXISTS idx_vend ON vendas(server_id, data);
    """)
    db.commit()

def _migrate_v1_to_v2():
    """Configurações por guild + moderação + verificação + economia + XP."""
    db.executescript("""
    CREATE TABLE IF NOT EXISTS guild_config (
        guild_id INTEGER PRIMARY KEY,
        log_channel_id INTEGER DEFAULT 0,
        mod_log_channel_id INTEGER DEFAULT 0,
        welcome_channel_id INTEGER DEFAULT 0,
        welcome_message TEXT,
        goodbye_channel_id INTEGER DEFAULT 0,
        goodbye_message TEXT,
        verify_channel_id INTEGER DEFAULT 0,
        verified_role_id INTEGER DEFAULT 0,
        unverified_role_id INTEGER DEFAULT 0,
        autorole_id INTEGER DEFAULT 0,
        member_count_channel_id INTEGER DEFAULT 0,
        economy_currency TEXT DEFAULT 'TEWS Coins',
        economy_emoji TEXT DEFAULT '🪙',
        xp_enabled INTEGER DEFAULT 1,
        xp_per_message INTEGER DEFAULT 5,
        xp_cooldown INTEGER DEFAULT 60,
        levelup_channel_id INTEGER DEFAULT 0,
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS warnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        mod_id INTEGER NOT NULL, reason TEXT,
        created_at INTEGER NOT NULL, active INTEGER DEFAULT 1);
    CREATE INDEX IF NOT EXISTS idx_warn ON warnings(guild_id, user_id, active);

    CREATE TABLE IF NOT EXISTS punishments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        mod_id INTEGER NOT NULL, type TEXT NOT NULL,
        reason TEXT, duration INTEGER,
        created_at INTEGER NOT NULL, expires_at INTEGER);

    CREATE TABLE IF NOT EXISTS moderation_config (
        guild_id INTEGER PRIMARY KEY,
        automod_enabled INTEGER DEFAULT 1,
        anti_spam INTEGER DEFAULT 1,
        anti_links INTEGER DEFAULT 1,
        anti_invites INTEGER DEFAULT 1,
        anti_caps INTEGER DEFAULT 1,
        anti_mention INTEGER DEFAULT 1,
        anti_raid INTEGER DEFAULT 1,
        anti_repeat INTEGER DEFAULT 1,
        max_mentions INTEGER DEFAULT 5,
        max_caps_pct INTEGER DEFAULT 70,
        spam_threshold INTEGER DEFAULT 5,
        spam_window INTEGER DEFAULT 5,
        punishment TEXT DEFAULT 'timeout',
        punishment_duration INTEGER DEFAULT 600,
        bad_words TEXT DEFAULT '',
        whitelist_links TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS economy (
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        balance INTEGER DEFAULT 0, bank INTEGER DEFAULT 0,
        daily_streak INTEGER DEFAULT 0, last_daily INTEGER DEFAULT 0,
        last_work INTEGER DEFAULT 0, last_crime INTEGER DEFAULT 0,
        created_at INTEGER NOT NULL,
        PRIMARY KEY (guild_id, user_id));
    CREATE INDEX IF NOT EXISTS idx_eco ON economy(guild_id, balance DESC);

    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        amount INTEGER NOT NULL, type TEXT NOT NULL,
        detail TEXT, created_at INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS idx_tx ON transactions(guild_id, user_id, created_at);

    CREATE TABLE IF NOT EXISTS shop_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL, name TEXT NOT NULL,
        description TEXT, price INTEGER NOT NULL,
        role_id INTEGER DEFAULT 0, emoji TEXT DEFAULT '📦',
        stock INTEGER DEFAULT -1, active INTEGER DEFAULT 1);
    CREATE INDEX IF NOT EXISTS idx_shop ON shop_items(guild_id, active);

    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL, acquired_at INTEGER NOT NULL);

    CREATE TABLE IF NOT EXISTS levels (
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        xp INTEGER DEFAULT 0, level INTEGER DEFAULT 0,
        messages INTEGER DEFAULT 0, last_xp INTEGER DEFAULT 0,
        PRIMARY KEY (guild_id, user_id));
    CREATE INDEX IF NOT EXISTS idx_lvl ON levels(guild_id, xp DESC);

    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        channel_id INTEGER NOT NULL, subject TEXT,
        status TEXT DEFAULT 'open', claimed_by INTEGER DEFAULT 0,
        created_at INTEGER NOT NULL, closed_at INTEGER);
    CREATE INDEX IF NOT EXISTS idx_ticket ON tickets(guild_id, status);

    CREATE TABLE IF NOT EXISTS suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        content TEXT NOT NULL, message_id INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        upvotes INTEGER DEFAULT 0, downvotes INTEGER DEFAULT 0,
        created_at INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS idx_sug ON suggestions(guild_id, status);

    CREATE TABLE IF NOT EXISTS polls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        question TEXT NOT NULL, options TEXT NOT NULL,
        message_id INTEGER DEFAULT 0, channel_id INTEGER DEFAULT 0,
        ends_at INTEGER, created_at INTEGER NOT NULL);

    CREATE TABLE IF NOT EXISTS poll_votes (
        poll_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        option_idx INTEGER NOT NULL,
        PRIMARY KEY (poll_id, user_id));

    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        channel_id INTEGER NOT NULL, message TEXT NOT NULL,
        remind_at INTEGER NOT NULL, created_at INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS idx_remind ON reminders(remind_at);
    """)
    db.commit()

def _migrate_v2_to_v3():
    """Verificação OAuth2 (opcional)."""
    db.executescript("""
    CREATE TABLE IF NOT EXISTS verifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL UNIQUE,
        method TEXT NOT NULL, verified_at INTEGER NOT NULL,
        oauth_access_token TEXT, oauth_refresh_token TEXT,
        oauth_expires_at INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS verify_attempts (
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        attempted_at INTEGER NOT NULL,
        PRIMARY KEY (guild_id, user_id));
    """)
    db.commit()

MIGRATIONS = {
    0: _migrate_v0_to_v1,
    1: _migrate_v1_to_v2,
    2: _migrate_v2_to_v3,
}

def init_db():
    with _lock:
        cur = _ensure_version_table()
        while cur < SCHEMA_VERSION:
            fn = MIGRATIONS.get(cur)
            if fn is None:
                log.error("Migração faltando para versão %s", cur); break
            log.info("Migrando schema: v%s → v%s", cur, cur + 1)
            fn()
            cur += 1
            _set_version(cur)
        # coluna legada
        cols = [r["name"] for r in db.execute("PRAGMA table_info(produtos)").fetchall()]
        if "categoria" not in cols:
            db.execute("ALTER TABLE produtos ADD COLUMN categoria TEXT DEFAULT 'Geral'")
            db.commit()
    log.info("✅ DB pronto (v%s)", SCHEMA_VERSION)

# ---- API pública ----
def run(q, p=()):
    with _lock:
        c = db.execute(q, p); db.commit(); return c

def get(q, p=()):
    return db.execute(q, p).fetchone()

def all_(q, p=()):
    return db.execute(q, p).fetchall()

def now() -> int:
    return int(time.time())
