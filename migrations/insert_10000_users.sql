-- Delete existing users with IDs 1-10000 (if any)
DELETE FROM "users" WHERE "id" >= 1 AND "id" <= 10000;

-- Insert 10,000 users with IDs from 1 to 10000
INSERT INTO "users" ("id", "username", "hash", "salt", "text", "created_at", "updated_at")
SELECT 
    s.id,
    'user' || s.id as username,
    'hash_' || s.id as hash,
    'salt_' || s.id as salt,
    'This is text for user ' || s.id as text,
    now() - (random() * interval '365 days') as created_at,
    now() - (random() * interval '365 days') as updated_at
FROM generate_series(1, 10000) AS s(id)
ON CONFLICT (id) DO UPDATE SET
    username = EXCLUDED.username,
    hash = EXCLUDED.hash,
    salt = EXCLUDED.salt,
    text = EXCLUDED.text,
    created_at = EXCLUDED.created_at,
    updated_at = EXCLUDED.updated_at;

