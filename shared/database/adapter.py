import os
import time
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
import aiosqlite

try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False

from shared.config_base import shared_config

logger = logging.getLogger(__name__)

class DatabaseAdapter:
    def __init__(self, db_url: str = "", sqlite_path: str = ""):
        self.db_url = db_url or shared_config.DATABASE_URL
        if os.getenv("VERCEL"):
            self.sqlite_path = "/tmp/shared_empire.db"
        else:
            self.sqlite_path = sqlite_path or shared_config.SQLITE_PATH
        self.is_postgres = bool(self.db_url and ("postgres://" in self.db_url or "postgresql://" in self.db_url))
        self.pg_pool = None

    async def init(self):
        """Initializes tables for either PostgreSQL or SQLite."""
        if self.is_postgres:
            if not HAS_ASYNCPG:
                raise ImportError("asyncpg is required for PostgreSQL. Please install asyncpg.")
            logger.info("Initializing PostgreSQL pool and schema...")
            # Normalize schema URL for asyncpg if needed
            pg_url = self.db_url.replace("postgres://", "postgresql://")
            self.pg_pool = await asyncpg.create_pool(pg_url, min_size=2, max_size=20)
            async with self.pg_pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        language TEXT DEFAULT 'en',
                        is_vip INT DEFAULT 0,
                        vip_until BIGINT DEFAULT 0,
                        referrer_id BIGINT DEFAULT NULL,
                        referral_count INT DEFAULT 0,
                        created_at BIGINT
                    );
                    CREATE TABLE IF NOT EXISTS bot_usage (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        bot_name TEXT NOT NULL,
                        date_str TEXT NOT NULL,
                        count INT DEFAULT 0,
                        UNIQUE(user_id, bot_name, date_str)
                    );
                    CREATE TABLE IF NOT EXISTS sponsors (
                        id SERIAL PRIMARY KEY,
                        channel_id TEXT NOT NULL,
                        channel_username TEXT,
                        title TEXT NOT NULL,
                        invite_link TEXT NOT NULL,
                        target_subs INT NOT NULL,
                        delivered_subs INT DEFAULT 0,
                        is_active INT DEFAULT 1,
                        owner_id BIGINT DEFAULT 0,
                        created_at BIGINT
                    );
                    CREATE TABLE IF NOT EXISTS user_sponsor_history (
                        user_id BIGINT,
                        sponsor_id INT,
                        verified_at BIGINT,
                        PRIMARY KEY(user_id, sponsor_id)
                    );
                    CREATE TABLE IF NOT EXISTS invoices (
                        invoice_id TEXT PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        bot_name TEXT,
                        target_subs INT DEFAULT 0,
                        amount_usd REAL NOT NULL,
                        pay_url TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at BIGINT
                    );
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at BIGINT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS user_personas (
                        user_id BIGINT PRIMARY KEY,
                        persona TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_bot_usage ON bot_usage(user_id, bot_name, date_str);
                    CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history(user_id, created_at);
                """)
        else:
            logger.info(f"Initializing SQLite database at: {self.sqlite_path}")
            os.makedirs(os.path.dirname(os.path.abspath(self.sqlite_path)), exist_ok=True)
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        language TEXT DEFAULT 'en',
                        is_vip INTEGER DEFAULT 0,
                        vip_until INTEGER DEFAULT 0,
                        referrer_id INTEGER DEFAULT NULL,
                        referral_count INTEGER DEFAULT 0,
                        created_at INTEGER
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS bot_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        bot_name TEXT NOT NULL,
                        date_str TEXT NOT NULL,
                        count INTEGER DEFAULT 0,
                        UNIQUE(user_id, bot_name, date_str)
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS sponsors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id TEXT NOT NULL,
                        channel_username TEXT,
                        title TEXT NOT NULL,
                        invite_link TEXT NOT NULL,
                        target_subs INTEGER NOT NULL,
                        delivered_subs INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        owner_id INTEGER DEFAULT 0,
                        created_at INTEGER
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_sponsor_history (
                        user_id INTEGER,
                        sponsor_id INTEGER,
                        verified_at INTEGER,
                        PRIMARY KEY(user_id, sponsor_id)
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS invoices (
                        invoice_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        bot_name TEXT,
                        target_subs INTEGER DEFAULT 0,
                        amount_usd REAL NOT NULL,
                        pay_url TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at INTEGER
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at INTEGER NOT NULL
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_personas (
                        user_id INTEGER PRIMARY KEY,
                        persona TEXT NOT NULL
                    )
                """)
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history(user_id, created_at)
                """)
                await db.commit()

    def _get_today_str(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    async def get_or_create_user(self, user_id: int, username: str = "", first_name: str = "", tg_lang: str = "en", referrer_id: Optional[int] = None) -> Dict[str, Any]:
        now = int(time.time())
        detected_lang = "en"
        if tg_lang:
            l = tg_lang.lower()
            if "ru" in l: detected_lang = "ru"
            elif "uz" in l: detected_lang = "uz"
            elif "es" in l: detected_lang = "es"

        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
                if not row:
                    ref_id = referrer_id if (referrer_id and referrer_id != user_id) else None
                    await conn.execute("""
                        INSERT INTO users (user_id, username, first_name, language, created_at, referrer_id)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (user_id) DO NOTHING
                    """, user_id, username or "", first_name or "", detected_lang, now, ref_id)
                    if ref_id:
                        await conn.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id = $1", ref_id)
                    row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
                user = dict(row)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                row = await cursor.fetchone()
                if not row:
                    ref_id = referrer_id if (referrer_id and referrer_id != user_id) else None
                    await db.execute("""
                        INSERT OR IGNORE INTO users (user_id, username, first_name, language, created_at, referrer_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (user_id, username or "", first_name or "", detected_lang, now, ref_id))
                    if ref_id:
                        await db.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?", (ref_id,))
                    await db.commit()
                    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                    row = await cursor.fetchone()
                user = dict(row)

        # Check VIP expiry
        if user.get("is_vip") and user.get("vip_until", 0) > 0 and user["vip_until"] < now:
            await self.revoke_vip(user_id)
            user["is_vip"] = 0

        return user

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        now = int(time.time())
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
                if not row: return None
                u = dict(row)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                row = await cursor.fetchone()
                if not row: return None
                u = dict(row)
        if u.get("is_vip") and u.get("vip_until", 0) > 0 and u["vip_until"] < now:
            await self.revoke_vip(user_id)
            u["is_vip"] = 0
        return u

    async def set_user_language(self, user_id: int, lang: str):
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                await conn.execute("UPDATE users SET language = $1 WHERE user_id = $2", lang, user_id)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
                await db.commit()

    async def set_user_vip(self, user_id: int, days: int = 30):
        now = int(time.time())
        vip_until = now + (days * 86400)
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                await conn.execute("UPDATE users SET is_vip = 1, vip_until = $1 WHERE user_id = $2", vip_until, user_id)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("UPDATE users SET is_vip = 1, vip_until = ? WHERE user_id = ?", (vip_until, user_id))
                await db.commit()

    async def revoke_vip(self, user_id: int):
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                await conn.execute("UPDATE users SET is_vip = 0, vip_until = 0 WHERE user_id = $1", user_id)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("UPDATE users SET is_vip = 0, vip_until = 0 WHERE user_id = ?", (user_id,))
                await db.commit()

    async def check_daily_quota(self, user_id: int, bot_name: str, limit: int) -> Tuple[bool, int, int]:
        """
        Returns (is_allowed, current_count, limit).
        VIP users always return (True, count, 999999).
        """
        user = await self.get_user(user_id)
        if user and user.get("is_vip"):
            return True, 0, 999999

        today_str = self._get_today_str()
        count = 0
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                val = await conn.fetchval(
                    "SELECT count FROM bot_usage WHERE user_id = $1 AND bot_name = $2 AND date_str = $3",
                    user_id, bot_name, today_str
                )
                if val is not None:
                    count = val
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                cursor = await db.execute(
                    "SELECT count FROM bot_usage WHERE user_id = ? AND bot_name = ? AND date_str = ?",
                    (user_id, bot_name, today_str)
                )
                row = await cursor.fetchone()
                if row:
                    count = row[0]

        is_allowed = count < limit
        return is_allowed, count, limit

    async def increment_daily_usage(self, user_id: int, bot_name: str) -> int:
        today_str = self._get_today_str()
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO bot_usage (user_id, bot_name, date_str, count)
                    VALUES ($1, $2, $3, 1)
                    ON CONFLICT (user_id, bot_name, date_str)
                    DO UPDATE SET count = bot_usage.count + 1
                """, user_id, bot_name, today_str)
                val = await conn.fetchval(
                    "SELECT count FROM bot_usage WHERE user_id = $1 AND bot_name = $2 AND date_str = $3",
                    user_id, bot_name, today_str
                )
                return val or 1
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("""
                    INSERT INTO bot_usage (user_id, bot_name, date_str, count)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT (user_id, bot_name, date_str)
                    DO UPDATE SET count = count + 1
                """, (user_id, bot_name, today_str))
                await db.commit()
                cursor = await db.execute(
                    "SELECT count FROM bot_usage WHERE user_id = ? AND bot_name = ? AND date_str = ?",
                    (user_id, bot_name, today_str)
                )
                row = await cursor.fetchone()
                return row[0] if row else 1

    async def get_active_sponsors(self) -> List[Dict[str, Any]]:
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM sponsors WHERE is_active = 1")
                return [dict(r) for r in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("SELECT * FROM sponsors WHERE is_active = 1")
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_all_sponsors(self) -> List[Dict[str, Any]]:
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM sponsors ORDER BY id DESC")
                return [dict(r) for r in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("SELECT * FROM sponsors ORDER BY id DESC")
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def add_sponsor(self, channel_id: str, channel_username: str, title: str, invite_link: str, target_subs: int, owner_id: int = 0) -> int:
        now = int(time.time())
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                sp_id = await conn.fetchval("""
                    INSERT INTO sponsors (channel_id, channel_username, title, invite_link, target_subs, delivered_subs, is_active, owner_id, created_at)
                    VALUES ($1, $2, $3, $4, $5, 0, 1, $6, $7)
                    RETURNING id
                """, channel_id, channel_username, title, invite_link, target_subs, owner_id, now)
                return sp_id
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                cursor = await db.execute("""
                    INSERT INTO sponsors (channel_id, channel_username, title, invite_link, target_subs, delivered_subs, is_active, owner_id, created_at)
                    VALUES (?, ?, ?, ?, ?, 0, 1, ?, ?)
                """, (channel_id, channel_username, title, invite_link, target_subs, owner_id, now))
                await db.commit()
                return cursor.lastrowid

    async def record_sponsor_delivery(self, user_id: int, sponsor_id: int):
        now = int(time.time())
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                inserted = await conn.execute("""
                    INSERT INTO user_sponsor_history (user_id, sponsor_id, verified_at)
                    VALUES ($1, $2, $3)
                    ON CONFLICT DO NOTHING
                """, user_id, sponsor_id, now)
                if "INSERT 0 1" in inserted:
                    await conn.execute("""
                        UPDATE sponsors 
                        SET delivered_subs = delivered_subs + 1,
                            is_active = CASE WHEN delivered_subs + 1 >= target_subs THEN 0 ELSE 1 END
                        WHERE id = $1
                    """, sponsor_id)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                cursor = await db.execute("""
                    INSERT OR IGNORE INTO user_sponsor_history (user_id, sponsor_id, verified_at)
                    VALUES (?, ?, ?)
                """, (user_id, sponsor_id, now))
                if cursor.rowcount > 0:
                    await db.execute("""
                        UPDATE sponsors 
                        SET delivered_subs = delivered_subs + 1,
                            is_active = CASE WHEN delivered_subs + 1 >= target_subs THEN 0 ELSE 1 END
                        WHERE id = ?
                    """, (sponsor_id,))
                    await db.commit()

    async def get_all_user_ids(self) -> List[int]:
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch("SELECT user_id FROM users")
                return [r["user_id"] for r in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                cursor = await db.execute("SELECT user_id FROM users")
                rows = await cursor.fetchall()
                return [r[0] for r in rows]

    async def get_network_stats(self) -> Dict[str, Any]:
        today_str = self._get_today_str()
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                total_users = await conn.fetchval("SELECT COUNT(*) FROM users") or 0
                vip_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_vip = 1") or 0
                active_sponsors = await conn.fetchval("SELECT COUNT(*) FROM sponsors WHERE is_active = 1") or 0
                today_actions = await conn.fetchval("SELECT SUM(count) FROM bot_usage WHERE date_str = $1", today_str) or 0
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM users")
                total_users = (await cursor.fetchone())[0]
                cursor = await db.execute("SELECT COUNT(*) FROM users WHERE is_vip = 1")
                vip_users = (await cursor.fetchone())[0]
                cursor = await db.execute("SELECT COUNT(*) FROM sponsors WHERE is_active = 1")
                active_sponsors = (await cursor.fetchone())[0]
                cursor = await db.execute("SELECT SUM(count) FROM bot_usage WHERE date_str = ?", (today_str,))
                row = await cursor.fetchone()
                today_actions = row[0] if (row and row[0]) else 0

        return {
            "total_users": total_users,
            "vip_users": vip_users,
            "active_sponsors": active_sponsors,
            "today_actions": today_actions
        }

    # ================= Chat Session & History Persistence =================
    async def add_chat_message(self, user_id: int, role: str, content: str):
        """Saves a single conversation turn (user or assistant) to persistent storage."""
        now = int(time.time())
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO chat_history (user_id, role, content, created_at) VALUES ($1, $2, $3, $4)",
                    user_id, role, content, now
                )
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute(
                    "INSERT INTO chat_history (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                    (user_id, role, content, now)
                )
                await db.commit()

    async def get_chat_history(self, user_id: int, limit: int = 10) -> List[Dict[str, str]]:
        """Returns the most recent N conversation turns in chronological order."""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT role, content FROM chat_history WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
                    user_id, limit
                )
                return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                cursor = await db.execute(
                    "SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                    (user_id, limit)
                )
                rows = await cursor.fetchall()
                return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    async def clear_chat_history(self, user_id: int) -> int:
        """Deletes all conversation history for the user and returns count of deleted turns."""
        count = 0
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                count = await conn.fetchval("SELECT COUNT(*) FROM chat_history WHERE user_id = $1", user_id) or 0
                await conn.execute("DELETE FROM chat_history WHERE user_id = $1", user_id)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM chat_history WHERE user_id = ?", (user_id,))
                row = await cursor.fetchone()
                count = row[0] if row else 0
                await db.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
                await db.commit()
        return count

    async def get_chat_message_count(self, user_id: int) -> int:
        """Returns current number of saved messages for user."""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                return await conn.fetchval("SELECT COUNT(*) FROM chat_history WHERE user_id = $1", user_id) or 0
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM chat_history WHERE user_id = ?", (user_id,))
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def set_user_persona(self, user_id: int, persona: str):
        """Persists the user's selected AI persona."""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO user_personas (user_id, persona) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET persona = EXCLUDED.persona",
                    user_id, persona
                )
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute(
                    "INSERT INTO user_personas (user_id, persona) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET persona = excluded.persona",
                    (user_id, persona)
                )
                await db.commit()

    async def get_user_persona(self, user_id: int) -> str:
        """Retrieves user's active persona or returns default 'general'."""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                val = await conn.fetchval("SELECT persona FROM user_personas WHERE user_id = $1", user_id)
                return val or "general"
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                cursor = await db.execute("SELECT persona FROM user_personas WHERE user_id = ?", (user_id,))
                row = await cursor.fetchone()
                return row[0] if (row and row[0]) else "general"

db = DatabaseAdapter()
