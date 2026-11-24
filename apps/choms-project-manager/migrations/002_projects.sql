CREATE TABLE pm_projects (
    id text PRIMARY KEY CHECK (id ~ '^[A-Za-z0-9_-]{1,100}$'),
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    schedule jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(schedule) = 'object')
);

INSERT INTO pm_projects (id, payload)
SELECT 'initial-project', '{"title":"Proyecto existente","start":null,"end":null}'::jsonb
WHERE EXISTS (SELECT 1 FROM career_records);

ALTER TABLE career_records ADD COLUMN project_id text REFERENCES pm_projects (id);
UPDATE career_records SET project_id = 'initial-project';
ALTER TABLE career_records ALTER COLUMN project_id SET NOT NULL;
ALTER TABLE career_records DROP CONSTRAINT career_records_pkey;
ALTER TABLE career_records ADD PRIMARY KEY (project_id, kind, id);

CREATE TABLE pm_templates (
    id text PRIMARY KEY CHECK (id ~ '^[A-Za-z0-9_-]{1,100}$'),
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object')
);
