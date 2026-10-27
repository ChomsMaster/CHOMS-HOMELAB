CREATE TABLE IF NOT EXISTS choms_memory.schema_version(version integer PRIMARY KEY);
CREATE TABLE IF NOT EXISTS choms_memory.records (
 id uuid PRIMARY KEY, lineage_id uuid NOT NULL, body jsonb,
 scope text NOT NULL CHECK(scope IN ('global','personal','project')),
 project text NOT NULL, topic text NOT NULL,
 state text NOT NULL CHECK(state IN ('candidate','active','superseded','expired','purge_pending')),
 revision integer NOT NULL CHECK(revision>0), vector_info jsonb,
 projection_state text NOT NULL CHECK(projection_state IN ('none','pending','ready','purge_pending')),
 content_hash text
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_topic ON choms_memory.records(scope,project,topic) WHERE state='active';
CREATE INDEX IF NOT EXISTS memory_scope ON choms_memory.records(scope,project,state);
CREATE TABLE IF NOT EXISTS choms_memory.receipts(
 request_id uuid PRIMARY KEY, operation text NOT NULL, target_id uuid NOT NULL,
 fingerprint text NOT NULL
);
CREATE TABLE IF NOT EXISTS choms_memory.tombstones(
 id uuid PRIMARY KEY, state text NOT NULL CHECK(state='forgotten'),
 revision integer NOT NULL, request_ids uuid[] NOT NULL
);
INSERT INTO choms_memory.schema_version VALUES(1) ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS choms_memory.purge_jobs (
 id uuid PRIMARY KEY, members uuid[] NOT NULL, request_ids uuid[] NOT NULL
);
