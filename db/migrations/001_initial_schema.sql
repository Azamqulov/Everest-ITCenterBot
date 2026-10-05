-- =====================================================================
-- Everest IT Center Telegram Bot - Database Schema (PostgreSQL / Supabase)
-- =====================================================================

-- 1. Users
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    username TEXT,
    phone TEXT,
    language TEXT NOT NULL DEFAULT 'uz',
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'teacher', 'admin', 'superadmin')),
    referral_code TEXT UNIQUE NOT NULL,
    referred_by BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 2. Required Channels for Subscription
CREATE TABLE IF NOT EXISTS required_channels (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Contests
CREATE TABLE IF NOT EXISTS contests (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    starts_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ends_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'finished', 'archived')),
    winner_mode TEXT NOT NULL DEFAULT 'top_n' CHECK (winner_mode IN ('top_n', 'lottery', 'hybrid')),
    rules TEXT,
    banner TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contests_status ON contests(status);

-- 4. Contest Prizes
CREATE TABLE IF NOT EXISTS contest_prizes (
    id SERIAL PRIMARY KEY,
    contest_id INT NOT NULL REFERENCES contests(id) ON DELETE CASCADE,
    place INT NOT NULL,
    description TEXT NOT NULL
);

-- 5. Referrals
CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    inviter_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    invitee_id BIGINT UNIQUE NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    contest_id INT REFERENCES contests(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'rejected', 'flagged')),
    confirmed_at TIMESTAMPTZ,
    flag_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_referrals_inviter ON referrals(inviter_id);
CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status);

-- 6. Points Ledger (Immutable Transaction Journal)
CREATE TABLE IF NOT EXISTS points_ledger (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    contest_id INT REFERENCES contests(id) ON DELETE SET NULL,
    amount INT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('referral', 'test', 'course', 'bonus', 'admin', 'penalty')),
    reference_id TEXT,
    reason TEXT NOT NULL,
    created_by BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_points_user ON points_ledger(user_id);
CREATE INDEX IF NOT EXISTS idx_points_contest ON points_ledger(contest_id);

-- 7. Teachers
CREATE TABLE IF NOT EXISTS teachers (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    bio TEXT,
    specialty TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. Courses
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    teacher_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE RESTRICT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'Boshlang''ich',
    price BIGINT NOT NULL DEFAULT 0,
    discount_price BIGINT,
    duration TEXT NOT NULL,
    schedule JSONB NOT NULL DEFAULT '{}'::jsonb,
    format TEXT NOT NULL DEFAULT 'offline',
    address TEXT,
    seats INT NOT NULL DEFAULT 15,
    starts_at DATE,
    trial_available BOOLEAN NOT NULL DEFAULT TRUE,
    banner TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('draft', 'pending', 'published', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_courses_status ON courses(status);
CREATE INDEX IF NOT EXISTS idx_courses_category ON courses(category);

-- 9. Course Enrollments
CREATE TABLE IF NOT EXISTS course_enrollments (
    id SERIAL PRIMARY KEY,
    course_id INT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    age INT,
    preferred_time TEXT,
    note TEXT,
    status TEXT NOT NULL DEFAULT 'yangi' CHECK (status IN ('yangi', 'boglanildi', 'yozildi', 'rad_etildi', 'kutish_royxati')),
    teacher_note TEXT,
    contacted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_enrollments_course ON course_enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_user ON course_enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_status ON course_enrollments(status);

-- 10. Tests
CREATE TABLE IF NOT EXISTS tests (
    id SERIAL PRIMARY KEY,
    teacher_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    course_id INT REFERENCES courses(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    subject TEXT,
    code TEXT UNIQUE NOT NULL,
    question_count INT NOT NULL,
    options_count INT NOT NULL DEFAULT 4,
    answer_key JSONB NOT NULL,
    file_id TEXT,
    time_limit INT NOT NULL DEFAULT 30,
    max_attempts INT NOT NULL DEFAULT 1,
    opens_at TIMESTAMPTZ,
    closes_at TIMESTAMPTZ,
    show_answers_mode TEXT NOT NULL DEFAULT 'immediate' CHECK (show_answers_mode IN ('immediate', 'on_close', 'never')),
    status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published', 'closed', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tests_code ON tests(code);
CREATE INDEX IF NOT EXISTS idx_tests_teacher ON tests(teacher_id);

-- 11. Test Attempts
CREATE TABLE IF NOT EXISTS test_attempts (
    id SERIAL PRIMARY KEY,
    test_id INT NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    score INT NOT NULL DEFAULT 0,
    correct_count INT NOT NULL DEFAULT 0,
    total_questions INT NOT NULL DEFAULT 0,
    percentage REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'timed_out'))
);

CREATE INDEX IF NOT EXISTS idx_test_attempts_user_test ON test_attempts(user_id, test_id);

-- 12. Test Answers (Real-time draft saving per question)
CREATE TABLE IF NOT EXISTS test_answers (
    id SERIAL PRIMARY KEY,
    attempt_id INT NOT NULL REFERENCES test_attempts(id) ON DELETE CASCADE,
    question_no INT NOT NULL,
    chosen TEXT,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(attempt_id, question_no)
);

-- 13. Post Drafts
CREATE TABLE IF NOT EXISTS post_drafts (
    id SERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    params JSONB NOT NULL DEFAULT '{}'::jsonb,
    variants JSONB NOT NULL DEFAULT '[]'::jsonb,
    chosen_variant INT,
    final_text TEXT,
    media TEXT,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'ready', 'published', 'scheduled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 14. Channel Posts
CREATE TABLE IF NOT EXISTS channel_posts (
    id SERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL,
    draft_id INT NOT NULL REFERENCES post_drafts(id) ON DELETE CASCADE,
    message_id INT,
    scheduled_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'published', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 15. AI Logs
CREATE TABLE IF NOT EXISTS ai_logs (
    id SERIAL PRIMARY KEY,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    tokens_in INT NOT NULL DEFAULT 0,
    tokens_out INT NOT NULL DEFAULT 0,
    cost REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 16. Broadcasts
CREATE TABLE IF NOT EXISTS broadcasts (
    id SERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    media_type TEXT,
    media_file_id TEXT,
    segment JSONB NOT NULL DEFAULT '{"type": "all"}'::jsonb,
    scheduled_at TIMESTAMPTZ,
    sent_count INT NOT NULL DEFAULT 0,
    failed_count INT NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 17. Settings
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL
);

-- 18. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    actor_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 19. FAQ
CREATE TABLE IF NOT EXISTS faq (
    id SERIAL PRIMARY KEY,
    question_uz TEXT NOT NULL,
    answer_uz TEXT NOT NULL,
    question_ru TEXT NOT NULL,
    answer_ru TEXT NOT NULL,
    order_num INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
