CREATE TABLE IF NOT EXISTS characters (
  id TEXT PRIMARY KEY,
  account TEXT NOT NULL,
  slot INTEGER NOT NULL CHECK (slot BETWEEN 0 AND 3),
  profile TEXT NOT NULL,
  state TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 0,
  save_revision INTEGER NOT NULL DEFAULT 0,
  updated INTEGER NOT NULL,
  change_id TEXT NOT NULL DEFAULT '',
  UNIQUE (account, slot)
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS field_sessions (
  account TEXT PRIMARY KEY,
  actor TEXT NOT NULL UNIQUE,
  character_id TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('shared', 'solo')),
  area TEXT NOT NULL,
  pose TEXT NOT NULL,
  seen INTEGER NOT NULL,
  sequence INTEGER NOT NULL DEFAULT 0,
  runtime TEXT NOT NULL,
  response TEXT NOT NULL DEFAULT '{}',
  change_id TEXT NOT NULL DEFAULT ''
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS field_sessions_area ON field_sessions (area, seen);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS field_encounters (
  area TEXT PRIMARY KEY,
  state TEXT NOT NULL,
  revision INTEGER NOT NULL
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS character_rewards (
  character_id TEXT NOT NULL,
  source TEXT NOT NULL,
  reward TEXT NOT NULL,
  applied INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (character_id, source)
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS character_rewards_pending ON character_rewards (character_id, source) WHERE applied = 0;
