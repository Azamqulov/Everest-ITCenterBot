import os
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
import aiosqlite
try:
    import asyncpg
except ImportError:
    asyncpg = None

from bot.config import settings

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.is_postgres = bool(settings.DATABASE_URL and asyncpg)
        self.pg_pool: Optional[Any] = None
        self.sqlite_path = settings.SQLITE_DB_PATH
        self._lock = asyncio.Lock()

    async def init(self):
        """Initialize database connection pool or sqlite schema."""
        if self.is_postgres:
            try:
                logger.info("Connecting to PostgreSQL / Supabase...")
                self.pg_pool = await asyncpg.create_pool(
                    dsn=settings.DATABASE_URL,
                    min_size=2,
                    max_size=10
                )
                logger.info("PostgreSQL connection pool established.")
            except Exception as e:
                logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to SQLite.")
                self.is_postgres = False

        if not self.is_postgres:
            os.makedirs(os.path.dirname(self.sqlite_path) or ".", exist_ok=True)
            logger.info(f"Using SQLite database at {self.sqlite_path}")
            await self._init_sqlite_schema()

        await self._seed_defaults()

    async def _init_sqlite_schema(self):
        """Create sqlite tables if not exist."""
        async with aiosqlite.connect(self.sqlite_path) as db:
            await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                username TEXT,
                phone TEXT,
                language TEXT NOT NULL DEFAULT 'uz',
                role TEXT NOT NULL DEFAULT 'user',
                referral_code TEXT UNIQUE NOT NULL,
                referred_by INTEGER,
                is_blocked INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS required_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS contests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                starts_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ends_at TIMESTAMP NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                winner_mode TEXT NOT NULL DEFAULT 'top_n',
                rules TEXT,
                banner TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS contest_prizes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contest_id INTEGER NOT NULL,
                place INTEGER NOT NULL,
                description TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inviter_id INTEGER NOT NULL,
                invitee_id INTEGER UNIQUE NOT NULL,
                contest_id INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                confirmed_at TIMESTAMP,
                flag_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS points_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                contest_id INTEGER,
                amount INTEGER NOT NULL,
                source TEXT NOT NULL,
                reference_id TEXT,
                reason TEXT NOT NULL,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                bio TEXT,
                specialty TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                level TEXT NOT NULL DEFAULT 'Boshlang''ich',
                price INTEGER NOT NULL DEFAULT 0,
                discount_price INTEGER,
                duration TEXT NOT NULL,
                schedule TEXT NOT NULL DEFAULT '{}',
                format TEXT NOT NULL DEFAULT 'offline',
                address TEXT,
                seats INTEGER NOT NULL DEFAULT 15,
                starts_at TEXT,
                trial_available INTEGER NOT NULL DEFAULT 1,
                banner TEXT,
                status TEXT NOT NULL DEFAULT 'published',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS course_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                age INTEGER,
                preferred_time TEXT,
                note TEXT,
                status TEXT NOT NULL DEFAULT 'yangi',
                teacher_note TEXT,
                contacted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                course_id INTEGER,
                title TEXT NOT NULL,
                subject TEXT,
                code TEXT UNIQUE NOT NULL,
                question_count INTEGER NOT NULL,
                options_count INTEGER NOT NULL DEFAULT 4,
                answer_key TEXT NOT NULL,
                file_id TEXT,
                time_limit INTEGER NOT NULL DEFAULT 30,
                max_attempts INTEGER NOT NULL DEFAULT 1,
                opens_at TIMESTAMP,
                closes_at TIMESTAMP,
                show_answers_mode TEXT NOT NULL DEFAULT 'immediate',
                status TEXT NOT NULL DEFAULT 'published',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS test_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                score INTEGER NOT NULL DEFAULT 0,
                correct_count INTEGER NOT NULL DEFAULT 0,
                total_questions INTEGER NOT NULL DEFAULT 0,
                percentage REAL NOT NULL DEFAULT 0.0,
                status TEXT NOT NULL DEFAULT 'in_progress'
            );

            CREATE TABLE IF NOT EXISTS test_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                question_no INTEGER NOT NULL,
                chosen TEXT,
                is_correct INTEGER NOT NULL DEFAULT 0,
                UNIQUE(attempt_id, question_no)
            );

            CREATE TABLE IF NOT EXISTS post_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                params TEXT NOT NULL DEFAULT '{}',
                variants TEXT NOT NULL DEFAULT '[]',
                chosen_variant INTEGER,
                final_text TEXT,
                media TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS channel_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                draft_id INTEGER NOT NULL,
                message_id INTEGER,
                scheduled_at TIMESTAMP,
                published_at TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS ai_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                tokens_in INTEGER NOT NULL DEFAULT 0,
                tokens_out INTEGER NOT NULL DEFAULT 0,
                cost REAL NOT NULL DEFAULT 0.0,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                media_type TEXT,
                media_file_id TEXT,
                segment TEXT NOT NULL DEFAULT '{"type": "all"}',
                scheduled_at TIMESTAMP,
                sent_count INTEGER NOT NULL DEFAULT 0,
                failed_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                entity TEXT NOT NULL,
                entity_id TEXT,
                details TEXT NOT NULL DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_uz TEXT NOT NULL,
                answer_uz TEXT NOT NULL,
                question_ru TEXT NOT NULL,
                answer_ru TEXT NOT NULL,
                order_num INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1
            );
            """)
            await db.commit()

    async def _seed_defaults(self):
        """Seed initial channels, settings, sample courses, and superadmins."""
        # 1. Superadmins roles
        for admin_id in settings.superadmin_list:
            user = await self.fetch_one("SELECT * FROM users WHERE telegram_id = ?", (admin_id,))
            if user:
                await self.execute("UPDATE users SET role = 'superadmin' WHERE telegram_id = ?", (admin_id,))

        # 2. Required channel default
        channels = await self.fetch_all("SELECT * FROM required_channels")
        if not channels and settings.DEFAULT_CHANNEL_ID:
            chat_id = int(settings.DEFAULT_CHANNEL_ID) if settings.DEFAULT_CHANNEL_ID.lstrip("-").isdigit() else -1001234567890
            await self.execute(
                "INSERT INTO required_channels (chat_id, title, link, is_active) VALUES (?, ?, ?, 1)",
                (chat_id, "Everest IT Center", settings.DEFAULT_CHANNEL_LINK)
            )

        # 3. Settings default
        ref_points = await self.fetch_one("SELECT value FROM settings WHERE key = 'referral_points'")
        if not ref_points:
            await self.execute(
                "INSERT INTO settings (key, value) VALUES ('referral_points', ?)",
                (json.dumps(settings.DEFAULT_REFERRAL_POINTS),)
            )

        # 4. Default Sample Course if empty
        courses = await self.fetch_all("SELECT id FROM courses")
        if not courses:
            admin_id = settings.superadmin_list[0] if settings.superadmin_list else 123456789
            # ensure admin user exists as placeholder teacher
            admin_user = await self.fetch_one("SELECT id FROM users WHERE telegram_id = ?", (admin_id,))
            if not admin_user:
                await self.execute(
                    "INSERT INTO users (telegram_id, full_name, role, referral_code) VALUES (?, ?, ?, ?)",
                    (admin_id, "Super Admin", "superadmin", "EV-ADMIN")
                )
            
            await self.execute("""
                INSERT INTO courses (
                    teacher_id, title, category, description, level, price, duration,
                    schedule, format, address, seats, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                admin_id,
                "Python Backend Dasturlash",
                "Backend",
                "Django, FastAPI, PostgreSQL, aiogram va Docker texnologiyalarini noldan o'rganing.",
                "Boshlang'ich",
                750000,
                "6 oy / 72 dars",
                json.dumps({"days": ["Dushanba", "Chorshanba", "Juma"], "time": "18:30 - 20:30"}),
                "Offline",
                "Chilonzor filiali, 4-qavat",
                12,
                "published"
            ))

            await self.execute("""
                INSERT INTO courses (
                    teacher_id, title, category, description, level, price, duration,
                    schedule, format, address, seats, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                admin_id,
                "Frontend Web Development",
                "Frontend",
                "HTML5, CSS3, JavaScript, Vue.js, Tailwind CSS va zamonaviy veb ilovalar.",
                "Boshlang'ich",
                700000,
                "5 oy / 60 dars",
                json.dumps({"days": ["Seshanba", "Payshanba", "Shanba"], "time": "15:00 - 17:00"}),
                "Offline",
                "Chilonzor filiali, 4-qavat",
                15,
                "published"
            ))

        # 5. Default Active Contest if none
        contests = await self.fetch_all("SELECT id FROM contests WHERE status = 'active'")
        if not contests:
            await self.execute("""
                INSERT INTO contests (title, description, ends_at, status, winner_mode, rules)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "Kuzgi Dasturchilar Konkursi 🚀",
                "Do'stlaringizni taklif qiling, test topshiring va qimmatbaho sovrinlarni yutib oling!",
                "2026-11-01 23:59:59",
                "active",
                "top_n",
                "1. Botga do'stlaringizni taklif qiling.\n2. Do'stingiz kanalga a'zo bo'lib raqamini tasdiqlashi shart.\n3. Har bir tasdiqlangan do'st uchun +10 ball.\n4. Soxta va bot akkauntlar qat'iyan taqiqlanadi!"
            ))
            # get contest id
            new_c = await self.fetch_one("SELECT id FROM contests ORDER BY id DESC LIMIT 1")
            if new_c:
                c_id = new_c["id"]
                await self.execute("INSERT INTO contest_prizes (contest_id, place, description) VALUES (?, 1, 'MacBook Air M2 💻')", (c_id,))
                await self.execute("INSERT INTO contest_prizes (contest_id, place, description) VALUES (?, 2, 'iPad 10th Gen 📱')", (c_id,))
                await self.execute("INSERT INTO contest_prizes (contest_id, place, description) VALUES (?, 3, 'AirPods Pro 2 🎧')", (c_id,))

    def _convert_query(self, query: str) -> str:
        """Convert '?' to '$1, $2' if postgres."""
        if not self.is_postgres:
            return query
        parts = query.split("?")
        if len(parts) == 1:
            return query
        res = []
        for i, part in enumerate(parts[:-1]):
            res.append(part)
            res.append(f"${i+1}")
        res.append(parts[-1])
        return "".join(res)

    async def execute(self, query: str, params: Union[tuple, list] = ()) -> Any:
        query = self._convert_query(query)
        if self.is_postgres and self.pg_pool:
            async with self.pg_pool.acquire() as conn:
                return await conn.execute(query, *params)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, params)
                await db.commit()
                return cursor.lastrowid

    async def fetch_one(self, query: str, params: Union[tuple, list] = ()) -> Optional[Dict[str, Any]]:
        query = self._convert_query(query)
        if self.is_postgres and self.pg_pool:
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow(query, *params)
                return dict(row) if row else None
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(query, params) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None

    async def fetch_all(self, query: str, params: Union[tuple, list] = ()) -> List[Dict[str, Any]]:
        query = self._convert_query(query)
        if self.is_postgres and self.pg_pool:
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(r) for r in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(r) for r in rows]

    async def fetch_val(self, query: str, params: Union[tuple, list] = ()) -> Any:
        row = await self.fetch_one(query, params)
        if row:
            return next(iter(row.values()))
        return None

db = DatabaseService()
