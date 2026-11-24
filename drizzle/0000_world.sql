CREATE TABLE IF NOT EXISTS world_presence (
  account TEXT PRIMARY KEY,
  actor TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  region INTEGER NOT NULL,
  seen INTEGER NOT NULL,
  pose TEXT NOT NULL
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS world_presence_region ON world_presence (region, seen);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS world_combat (
  region INTEGER PRIMARY KEY,
  revision INTEGER NOT NULL,
  last_change TEXT NOT NULL,
  state TEXT NOT NULL
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS world_rewards (
  actor TEXT NOT NULL,
  event TEXT NOT NULL,
  monster INTEGER NOT NULL,
  x INTEGER NOT NULL,
  issued INTEGER NOT NULL,
  PRIMARY KEY (actor, event)
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS world_rewards_issued ON world_rewards (issued);
