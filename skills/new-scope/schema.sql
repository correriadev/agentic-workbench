CREATE TABLE IF NOT EXISTS spec_meta (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    change_id TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN (
        'intent','requirement','acceptance','business_rule','constraint','assumption',
        'decision','risk','component','method','api_contract','request_field',
        'response_field','state_transition','task','test_scenario','assertion',
        'verification_obligation','evidence','gap','behavior','error_contract')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN (
        'confirmed','observed','proposed','planned','pending','blocked',
        'applicable','not_applicable','superseded','resolved')),
    origin TEXT NOT NULL CHECK (origin IN ('human','repository','inference','catalog','execution')),
    details TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(details)),
    CHECK (state <> 'confirmed' OR origin = 'human')
);
CREATE TABLE IF NOT EXISTS edges (
    src TEXT NOT NULL REFERENCES nodes(id),
    relation TEXT NOT NULL CHECK (relation IN (
        'requires','depends_on','implements','verified_by','covers','threatens',
        'mitigates','supports','contradicts','supersedes','references','produces','consumes',
        'has_request','has_response','has_error','has_assertion')),
    dst TEXT NOT NULL REFERENCES nodes(id),
    rationale TEXT NOT NULL,
    PRIMARY KEY (src, relation, dst)
);
CREATE INDEX IF NOT EXISTS edges_incoming ON edges(dst, relation);
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY NOT NULL,
    project_root TEXT NOT NULL,
    path TEXT NOT NULL,
    symbol TEXT,
    line_start INTEGER,
    line_end INTEGER,
    version TEXT,
    sha256 TEXT NOT NULL,
    excerpt TEXT,
    CHECK ((line_start IS NULL AND line_end IS NULL) OR
           (line_start IS NOT NULL AND line_end IS NOT NULL AND
            line_start >= 1 AND line_end >= line_start))
);
CREATE TABLE IF NOT EXISTS node_sources (
    node_id TEXT NOT NULL REFERENCES nodes(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    PRIMARY KEY (node_id, source_id)
);
CREATE TABLE IF NOT EXISTS task_details (
    task_id TEXT PRIMARY KEY NOT NULL REFERENCES nodes(id),
    project_root TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('implementation','evidence')),
    unit_command TEXT,
    runner_source TEXT REFERENCES sources(id),
    red TEXT,
    green TEXT
);
CREATE TABLE IF NOT EXISTS task_files (
    task_id TEXT NOT NULL REFERENCES task_details(task_id),
    path TEXT NOT NULL,
    origin TEXT NOT NULL CHECK (origin IN ('existing','new')),
    role TEXT NOT NULL CHECK (role IN ('unit','production','support')),
    PRIMARY KEY (task_id, path)
);
CREATE TABLE IF NOT EXISTS verification_cases (
    scenario_id TEXT PRIMARY KEY NOT NULL REFERENCES nodes(id),
    level TEXT NOT NULL CHECK (level IN ('unit','integration','e2e','manual')),
    conditions TEXT NOT NULL,
    steps TEXT NOT NULL,
    expected TEXT NOT NULL,
    command TEXT
);
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY NOT NULL REFERENCES nodes(id),
    scenario_id TEXT NOT NULL REFERENCES verification_cases(scenario_id),
    plan_revision INTEGER NOT NULL CHECK (plan_revision > 0),
    candidate TEXT NOT NULL,
    environment TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    command TEXT NOT NULL,
    exit_code INTEGER NOT NULL,
    observations TEXT NOT NULL CHECK (json_valid(observations)),
    artifact TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS history (
    revision INTEGER PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE,
    digest TEXT NOT NULL,
    reason TEXT NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changes TEXT NOT NULL CHECK (json_valid(changes))
);
