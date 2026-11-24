CREATE TABLE career_records (
    kind text NOT NULL CHECK (kind IN ('tasks', 'activities', 'plan')),
    id text NOT NULL CHECK (id ~ '^[A-Za-z0-9_-]{1,100}$'),
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    PRIMARY KEY (kind, id)
);
