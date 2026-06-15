-- Lux Leti AI Mentor — ma'lumotlar bazasi sxemasi (idempotent).

CREATE TABLE IF NOT EXISTS students (
    chat_id         BIGINT PRIMARY KEY,
    full_name       TEXT        NOT NULL DEFAULT 'Anonim',
    level           INTEGER     NOT NULL DEFAULT 1,
    active_topic    TEXT,
    weak_topics     TEXT[]      NOT NULL DEFAULT '{}',
    mastered_topics TEXT[]      NOT NULL DEFAULT '{}',
    last_active     TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Eski 'students' jadvalini (n8n davridan qolgan) yangi sxemaga moslashtirish.
-- Idempotent: ustun bor bo'lsa/tip to'g'ri bo'lsa qayta ishlatishda no-op.
ALTER TABLE students ADD COLUMN IF NOT EXISTS active_topic    TEXT;
ALTER TABLE students ADD COLUMN IF NOT EXISTS weak_topics     TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE students ADD COLUMN IF NOT EXISTS mastered_topics TEXT[] NOT NULL DEFAULT '{}';

-- level: eski TEXT bo'lsa INTEGER ga o'tkazish (eski default integerga
-- avtomatik o'tmagani uchun avval DROP DEFAULT).
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'students' AND column_name = 'level'
           AND data_type = 'text'
    ) THEN
        ALTER TABLE students ALTER COLUMN level DROP DEFAULT;
        ALTER TABLE students
            ALTER COLUMN level TYPE INTEGER USING NULLIF(level, '')::integer;
    END IF;
END $$;
UPDATE students SET level = 1 WHERE level IS NULL;
ALTER TABLE students ALTER COLUMN level SET DEFAULT 1;
ALTER TABLE students ALTER COLUMN level SET NOT NULL;

-- weak_topics / mastered_topics: eski TEXT bo'lsa TEXT[] ga o'tkazish
-- (vergul bilan ajratilgan; bo'sh bo'lsa '{}').
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'students' AND column_name = 'weak_topics'
           AND data_type <> 'ARRAY'
    ) THEN
        ALTER TABLE students ALTER COLUMN weak_topics DROP DEFAULT;
        ALTER TABLE students ALTER COLUMN weak_topics TYPE TEXT[] USING (
            CASE WHEN coalesce(weak_topics::text, '') = '' THEN '{}'::text[]
                 ELSE string_to_array(weak_topics::text, ',') END
        );
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'students' AND column_name = 'mastered_topics'
           AND data_type <> 'ARRAY'
    ) THEN
        ALTER TABLE students ALTER COLUMN mastered_topics DROP DEFAULT;
        ALTER TABLE students ALTER COLUMN mastered_topics TYPE TEXT[] USING (
            CASE WHEN coalesce(mastered_topics::text, '') = '' THEN '{}'::text[]
                 ELSE string_to_array(mastered_topics::text, ',') END
        );
    END IF;
END $$;
ALTER TABLE students ALTER COLUMN weak_topics     SET DEFAULT '{}';
ALTER TABLE students ALTER COLUMN weak_topics     SET NOT NULL;
ALTER TABLE students ALTER COLUMN mastered_topics SET DEFAULT '{}';
ALTER TABLE students ALTER COLUMN mastered_topics SET NOT NULL;

-- last_active: eski tz'siz timestamp bo'lsa timestamptz ga (UTC sifatida).
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'students' AND column_name = 'last_active'
           AND data_type = 'timestamp without time zone'
    ) THEN
        ALTER TABLE students ALTER COLUMN last_active DROP DEFAULT;
        ALTER TABLE students
            ALTER COLUMN last_active TYPE TIMESTAMPTZ USING last_active AT TIME ZONE 'UTC';
    END IF;
END $$;
ALTER TABLE students ALTER COLUMN last_active SET DEFAULT now();

CREATE TABLE IF NOT EXISTS conversation_messages (
    id         BIGSERIAL PRIMARY KEY,
    chat_id    BIGINT      NOT NULL,
    role       TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
    content    TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conversation_chat_id
    ON conversation_messages (chat_id, id);

CREATE TABLE IF NOT EXISTS test_sessions (
    id              BIGSERIAL PRIMARY KEY,
    chat_id         BIGINT      NOT NULL,
    topic           TEXT        NOT NULL,
    questions       JSONB       NOT NULL,
    answers         JSONB       NOT NULL DEFAULT '[]',
    current_index   INTEGER     NOT NULL DEFAULT 0,
    status          TEXT        NOT NULL DEFAULT 'in_progress',
    score           INTEGER     NOT NULL DEFAULT 0,
    total_questions INTEGER     NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Eski o'rnatishlar uchun ustunlarni qo'shish (idempotent).
ALTER TABLE test_sessions ADD COLUMN IF NOT EXISTS score INTEGER NOT NULL DEFAULT 0;
ALTER TABLE test_sessions ADD COLUMN IF NOT EXISTS total_questions INTEGER NOT NULL DEFAULT 0;

-- Har bir o'quvchida bir vaqtda faqat bitta faol sessiya bo'lishi mumkin.
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_session
    ON test_sessions (chat_id)
    WHERE status = 'in_progress';

CREATE TABLE IF NOT EXISTS review_items (
    id            BIGSERIAL PRIMARY KEY,
    chat_id       BIGINT      NOT NULL,
    topic         TEXT        NOT NULL,
    box           INTEGER     NOT NULL DEFAULT 0,
    due_at        TIMESTAMPTZ NOT NULL,
    last_reviewed TIMESTAMPTZ,
    last_notified TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (chat_id, topic)
);

CREATE INDEX IF NOT EXISTS idx_review_due ON review_items (due_at);
